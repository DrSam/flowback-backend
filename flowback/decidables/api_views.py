from rest_framework.viewsets import ModelViewSet
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission

from flowback.decidables import models as decidable_models
from flowback.decidables import serializers as decidable_serializers
import django_filters
from flowback.decidables import rules as decidable_rules
from flowback.group.models import GroupUser
from flowback.group.models import Group
from flowback.decidables import filters as decidable_filters
from django.db.models import Subquery, OuterRef
from rest_framework.generics import get_object_or_404
from django.db.models import Sum
from flowback.decidables.fields import DecidableStateChoices
from flowback.decidables.fields import DecidableTypeChoices
from django.db.models import Case, When
from django.db.models import IntegerField
from nested_multipart_parser import NestedParser
from django_q.tasks import async_task
from flowback.decidables.fields import VoteTypeChoices
from feed.models import Channel
from feed.fields import ChannelTypechoices
from django.db.models import Q
from django.db.models import Value
from flowback.decidables.tasks import update_decidable_votes
from flowback.decidables.tasks import update_option_votes
from flowback.decidables.tasks import after_decidable_confirm
from flowback.decidables.tasks import after_decidable_create
from flowback.decidables.tasks import after_option_create


class DecidableViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            return decidable_rules.can_create_decidable.test(
                request.user.id,
                request.data.get('group')
            )
        return super().has_permission(request,view)

    def has_object_permission(self, request, view, obj):
        group = view.get_group()
        group_obj = decidable_models.GroupDecidableAccess.objects.get(
            group=group,
            decidable=obj
        )
        if view.action == 'transition':
            state = request.data.get('state')
            if not state:
                return False
            actions = group_obj.fsm.get_available_actions(request.user)
            if state not in actions:
                return False
            return True
        return super().has_object_permission(request,view,obj)


class DecidableViewSet(ModelViewSet):
    _group = None

    queryset = decidable_models.Decidable.objects
    serializer_class = decidable_serializers.DecidableListSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = decidable_filters.DecidableFilter
    permission_classes = [DecidableViewSetPermission]

    def get_group(self):
        if self._group:
            return self._group
        
        group_id = self.kwargs.get('group_id')
        group = Group.objects.get(id=group_id)
        self._group = group
        return self._group

    def get_group_decidable_access(self):
        if not self.detail:
            return
        decidable = self.get_object()
        group = self.get_group()
        group_decidable_access = decidable.group_decidable_access.filter(group=group).first()
        return group_decidable_access

    def annotate_queryset(self,queryset):
        queryset = queryset.annotate(
            votes=Subquery(
                decidable_models.GroupDecidableAccess.objects.filter(
                    group=self.get_group(),
                    decidable_id=OuterRef('id')
                ).values('value')[:1]
            ),
            user_vote=Subquery(
                decidable_models.GroupUserDecidableVote.objects.filter(
                    group_decidable_access__group=self.get_group(),
                    group_decidable_access__decidable_id=OuterRef('id'),
                    group_user__group=self.get_group(),
                    group_user__user=self.request.user
                ).values('value')[:1]
            )
        )
        return queryset

    def get_queryset(self):
        queryset = decidable_models.Decidable.objects.filter(groups=self.get_group())
        if self.action not in  ['update','partial_update','confirm']:
            queryset = queryset.filter(confirmed=True)
        if (
            'primary_decidable' not in self.request.query_params 
            and
            'parent_decidable' not in self.request.query_params
            and
            'parent_option' not in self.request.query_params
            and not
            self.detail
        ):
            queryset = queryset.filter(root_decidable__isnull=True)
        return queryset

    def get_decidables_rank(self,queryset):
        # Get main queryset.
        main_queryset = decidable_models.Decidable.objects.filter(groups=self.get_group())
        if self.action not in  ['update','partial_update','confirm']:
            main_queryset = main_queryset.filter(confirmed=True)
        if 'primary_decidable' in self.request.query_params:
            main_queryset = main_queryset.filter(primary_decidable=self.request.query_params.get('primary_decidable'))
        elif 'parent_decidable' in self.request.query_params:
            main_queryset = main_queryset.filter(parent_decidable=self.request.query_params.get('parent_decidable'))
        elif 'parent_option' in self.request.query_params:
            main_queryset = main_queryset.filter(parent_option=self.request.query_params.get('parent_option'))
        else:
            main_queryset = main_queryset.filter(root_decidable__isnull=True)

        main_queryset = main_queryset.exclude(decidable_type='linkfile')

        main_queryset = main_queryset.annotate(
            votes=Subquery(
                decidable_models.GroupDecidableAccess.objects.filter(
                    group=self.get_group(),
                    decidable_id=OuterRef('id')
                ).values('value')[:1]
            )
        ).values('id','votes')
        votes = sorted(list(set([dec['votes'] for dec in main_queryset])),reverse=True)
        ranks = [(vote,rank+1) for rank,vote in enumerate(votes)]
        whens = [
            When(votes=k, then=v) for (k,v) in ranks
        ]

        queryset = queryset.annotate(
            poll_rank=Case(
                *whens,
                default=999,
                output_field=IntegerField()
            ),
            total_poll_count=Value(main_queryset.count())
        )
        queryset = queryset.order_by('poll_rank')
        return queryset

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.annotate_queryset(queryset)
        queryset = self.get_decidables_rank(queryset)
        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['group'] = self.get_group()
        context['group_decidable_access'] = self.get_group_decidable_access()
        return context

    def get_serializer_class(self):
        if self.action in ['create','confirm','create_aspect']:
            return decidable_serializers.DecidableCreateSerializer
        elif self.action in ['aspect','transition']:
            return decidable_serializers.DecidableListSerializer
        elif self.action in ['results']:
            return decidable_serializers.DecidableResultSerializer
        elif not self.detail:
            return decidable_serializers.DecidableListSerializer
        else:
            return decidable_serializers.DecidableDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        queryset = self.annotate_queryset(queryset)
        queryset = self.get_decidables_rank(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        parser = NestedParser(request.data)
        if not parser.is_valid():
            return Response(parser.errors,status.HTTP_200_OK)

        data = parser.validate_data
        attachments = data.pop('attachments',[])

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)
        group_user = GroupUser.objects.filter(
            user=request.user,
            group=self.get_group()
        ).first()
        decidable = serializer.save(created_by=group_user)
        decidable.groups.add(self.get_group())

        for attachment in attachments:
            attachment['decidable'] = decidable.id

        attachment_serializer = decidable_serializers.AttachmentCreateSerializer(data=attachments,many=True)
        if attachment_serializer.is_valid():
            attachment_serializer.save()

        after_decidable_create(decidable.id)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['POST']
    )
    def confirm(self, request, *args, **kwargs):
        decidable = self.get_object()
        decidable.confirmed = True
        decidable.save()
        group_decidable_access = self.get_group_decidable_access()
        group_decidable_access.fsm.start_poll(user=request.user)
        group_decidable_access.save()

        after_decidable_confirm(decidable.id)
        
        return Response("OK",status.HTTP_200_OK)
    
    @action(
        detail=True,
        methods=['POST']
    )
    def reject(self, request, *args, **kwargs):
        decidable = self.get_object()
        decidable.delete()
        return Response("OK",status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['POST']
    )
    def vote(self, request, *args, **kwargs):
        decidable = self.get_object()

        if request.data.get('vote',None) is None:
            return Response("Vote not submitted",status.HTTP_400_BAD_REQUEST)
        
        update_decidable_votes(
            decidable.id,
            request.user.id,
            request.data.get('vote')
        )

        decidable = self.get_object()
        serializer = self.get_serializer(instance=decidable)
        return Response(serializer.data,status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['POST']
    )
    def transition(self, request, *args, **kwargs):
        decidable = self.get_object()
        group_decidable_access = self.get_group_decidable_access()
        getattr(group_decidable_access.fsm,request.data.get('state'))(user=request.user)
        group_decidable_access.save()
        serializer = self.get_serializer(decidable)
        return Response(serializer.data,status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['GET']
    )
    def results(self, request, *args, **kwargs):
        decidable = self.get_object()
        serializer = self.get_serializer(instance=decidable)
        return Response(serializer.data,status.HTTP_200_OK)




class AttachmentViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            return decidable_rules.can_create_attachment.test(
                request.user.id,
                request.data.get('group')
            )
        return super().has_permission(request,view)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request,view,obj)


class AttachmentViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = decidable_models.Attachment.objects
    serializer_class = decidable_serializers.AttachmentDetailSerializer
    permission_classes = [AttachmentViewSetPermission]


class OptionViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        return super().has_permission(request,view)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request,view,obj)


class OptionViewSet(
    ModelViewSet
):
    _group = None
    _decidable = None

    queryset = decidable_models.Option.objects
    serializer_class = decidable_serializers.OptionListSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = decidable_filters.OptionFilter
    permission_classes = [OptionViewSetPermission]

    def get_queryset(self):
        queryset = decidable_models.Option.objects.filter(
            decidables=self.get_decidable()
        )

        return queryset

    def annotate_queryset(self, queryset):
        queryset = queryset.annotate(
            votes=Subquery(
                decidable_models.GroupDecidableOptionAccess.objects.filter(
                    group=self.get_group(),
                    decidable_option__decidable_id=self.get_decidable().id,
                    decidable_option__option_id=OuterRef('id')
                ).values('value')[:1]
            ),
            quorum=Subquery(
                decidable_models.GroupDecidableOptionAccess.objects.filter(
                    group=self.get_group(),
                    decidable_option__decidable_id=self.get_decidable().id,
                    decidable_option__option_id=OuterRef('id')
                ).values('quorum')[:1]
            ),
            approval=Subquery(
                decidable_models.GroupDecidableOptionAccess.objects.filter(
                    group=self.get_group(),
                    decidable_option__decidable_id=self.get_decidable().id,
                    decidable_option__option_id=OuterRef('id')
                ).values('approval')[:1]
            ),
            passed_flag=Subquery(
                decidable_models.GroupDecidableOptionAccess.objects.filter(
                    group=self.get_group(),
                    decidable_option__decidable_id=self.get_decidable().id,
                    decidable_option__option_id=OuterRef('id')
                ).values('passed_flag')[:1]
            ),
            passed_timestamp=Subquery(
                decidable_models.GroupDecidableOptionAccess.objects.filter(
                    group=self.get_group(),
                    decidable_option__decidable_id=self.get_decidable().id,
                    decidable_option__option_id=OuterRef('id')
                ).values('passed_timestamp')[:1]
            ),
            winner=Subquery(
                decidable_models.GroupDecidableOptionAccess.objects.filter(
                    group=self.get_group(),
                    decidable_option__decidable_id=self.get_decidable().id,
                    decidable_option__option_id=OuterRef('id')
                ).values('winner')[:1]
            ),
            user_vote=Subquery(
                decidable_models.GroupUserDecidableOptionVote.objects.filter(
                    group_decidable_option_access__group=self.get_group(),
                    group_decidable_option_access__decidable_option__decidable_id=self.get_decidable().id,
                    group_decidable_option_access__decidable_option__option_id=OuterRef('id'),
                    group_user__group=self.get_group(),
                    group_user__user=self.request.user
                ).values('value')[:1]
            )
        )
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['group'] = self.get_group()
        context['decidable'] = self.get_decidable()
        return context

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.annotate_queryset(queryset)
        queryset = self.get_options_rank(queryset)
        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def get_group(self):
        if self._group:
            return self._group
        
        group_id = self.kwargs.get('group_id')
        group = Group.objects.get(id=group_id)
        self._group = group
        return self._group
    
    def get_decidable(self):
        if self._decidable:
            return self._decidable
        
        decidable_id = self.kwargs.get('decidable_id')
        decidable = decidable_models.Decidable.objects.get(id=decidable_id)
        self._decidable = decidable
        return self._decidable

    def get_options_rank(self,main_queryset):
        queryset = decidable_models.Option.objects.filter(
            decidables=self.get_decidable()
        ).annotate(
            votes=Subquery(
                decidable_models.GroupDecidableOptionAccess.objects.filter(
                    group=self.get_group(),
                    decidable_option__option__id=OuterRef('id'),
                    decidable_option__decidable=self.get_decidable()
                ).values('value')[:1]
            ),
        ).values('id','votes')
        votes = sorted(list(set([dec['votes'] for dec in queryset])),reverse=True)
        ranks = [(vote,rank+1) for rank,vote in enumerate(votes)]
        whens = [
            When(votes=k, then=v) for (k,v) in ranks
        ]

        main_queryset = main_queryset.annotate(
            option_rank=Case(
                *whens,
                default=0,
                output_field=IntegerField()
            ),
            total_option_count = Value(queryset.count())
        )
        main_queryset = main_queryset.order_by('option_rank')
        return main_queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return decidable_serializers.OptionCreateSerializer
        if not self.detail:
            return decidable_serializers.OptionListSerializer
        else:
            return decidable_serializers.OptionDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.annotate_queryset(queryset)
        queryset = self.get_options_rank(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        decidable = self.get_decidable()

        if decidable.decidable_type == 'aspect':
            raise Exception('Cannot add an option')

        parser = NestedParser(request.data)
        if not parser.is_valid():
            return Response(parser.errors,status.HTTP_200_OK)

        data = parser.validate_data
        attachments = data.pop('attachments',[])
        tags = data.pop('tags',[])

        group_user = GroupUser.objects.filter(
            user=request.user,
            group=self.get_group()
        ).first()
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)
        option = serializer.save(
            root_decidable = decidable.get_root_decidable(),
            created_by=group_user
        )
        option.decidables.add(decidable)

        # Add tags, and later whatever we need for the decidable_option
        decidable_option = decidable_models.DecidableOption.objects.get(
            decidable = self.get_decidable(),
            option = option
        )
        if len(tags)>0:
            decidable_option.tags = tags
            decidable_option.save()

    
        # Add attachments
        for attachment in attachments:
            attachment['option'] = option.id

        
        attachment_serializer = decidable_serializers.AttachmentCreateSerializer(data=attachments,many=True)
        if attachment_serializer.is_valid():
            attachment_serializer.save()

        # Add group
        for group in decidable.get_root_decidable().groups.all():
            decidable_option = decidable_models.DecidableOption.objects.get(
                decidable = self.get_decidable(),
                option = option
            )
            decidable_option.groups.add(group)

        if decidable.get_root_decidable().confirmed:
            after_option_create(option.id,decidable.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['POST']
    )
    def vote(self, request, *args, **kwargs):
        option = self.get_object()
        decidable = self.get_decidable()

        value = request.data.get('vote')
        if value is None:
            return Response("Vote missing",status.HTTP_400_BAD_REQUEST)
        
        #TODO: Move to async later
        update_option_votes(
            decidable.id,
            option.id,
            request.user.id,
            request.data.get('vote')
        )

        option = self.get_object()
        serializer = self.get_serializer(instance=option)
        return Response(serializer.data,status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['GET']
    )
    def results(self, request, *args, **kwargs):
        decidable = self.get_decidable()
        
        return Response("OK",status.HTTP_200_OK)
    