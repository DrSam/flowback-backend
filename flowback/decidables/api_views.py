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
from django.db.models import Case, When
from django.db.models import IntegerField
from nested_multipart_parser import NestedParser



class DecidableViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            return decidable_rules.can_create_decidable.test(
                request.user.id,
                request.data.get('group')
            )
        return super().has_permission(request,view)

    def has_object_permission(self, request, view, obj):
        if view.action == 'transition':
            state = request.data.get('state')
            if not state:
                return False
            actions = obj.fsm.get_available_actions(request.user)
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
        queryset = decidable_models.Decidable.objects.filter(
            groups=self.get_group(),
        )
        return queryset

    def get_decidables_rank(self,main_queryset,queryset=None):
        if queryset is None:
            queryset = decidable_models.Decidable.objects.filter(
            groups=self.get_group(),
            state=DecidableStateChoices.OPEN,
            root_decidable=None,
        )
        queryset = queryset.annotate(
            votes=Subquery(
                decidable_models.GroupDecidableAccess.objects.filter(
                    group=self.get_group(),
                    decidable_id=OuterRef('id')
                ).values('value')[:1]
            )
        ).values('id','votes')
        votes = sorted(list(set([dec['votes'] for dec in queryset])),reverse=True)
        ranks = [(vote,rank+1) for rank,vote in enumerate(votes)]
        whens = [
            When(votes=k, then=v) for (k,v) in ranks
        ]

        main_queryset = main_queryset.annotate(
            poll_rank=Case(
                *whens,
                default=0,
                output_field=IntegerField()
            )
        )
        main_queryset = main_queryset.order_by('poll_rank')
        return main_queryset

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
        return context

    def get_serializer_class(self):
        if self.action in ['create','confirm','create_aspect']:
            return decidable_serializers.DecidableCreateSerializer
        elif self.action in ['aspect']:
            return decidable_serializers.DecidableListSerializer
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
        serializer.is_valid(raise_exception=True)
        group_user = GroupUser.objects.filter(
            user=request.user,
            group_id=request.data.get('group')
        ).first()
        decidable = serializer.save(created_by=group_user)
        
        decidable.groups.add(self.get_group())

        for attachment in attachments:
            attachment['decidable'] = decidable.id

        
        attachment_serializer = decidable_serializers.AttachmentCreateSerializer(data=attachments,many=True)
        if attachment_serializer.is_valid():
            attachment_serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['POST']
    )
    def confirm(self, request, *args, **kwargs):
        decidable = self.get_object()
        decidable.confirmed = True
        decidable.save()



        
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
        
        # Get groups with access to decidable, that the user is a part of
        group_decidable_accesses = decidable.group_decidable_access.filter(
            group__groupuser__user=request.user,
            group__groupuser__active=True
        )

        # Set the user's vote for all of the above groups with the current vote
        for group_decidable_access in group_decidable_accesses:
            group_user = group_decidable_access.group.groupuser_set.get(
                user=request.user,
                active=True
            )
            decidable_models.GroupUserDecidableVote.objects.update_or_create(
                group_decidable_access=group_decidable_access,
                group_user=group_user,
                defaults={
                    'value':request.data.get('vote')
                }
            )

        # For each group, update votes
        for group_decidable_access in group_decidable_accesses:
            group_decidable_access.value = group_decidable_access.group_user_decidable_vote.aggregate(Sum('value'))['value__sum'] or 0
            group_decidable_access.save()

        return Response("OK",status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['POST']
    )
    def transition(self, request, *args, **kwargs):
        decidable = self.get_object()
        getattr(decidable.fsm,request.data.get('state'))(user=request.user)
        serializer = decidable_serializers.DecidableListSerializer(decidable)
        return Response(serializer.data,status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['GET']
    )
    def aspect(self, request, *args, **kwargs):
        primary_decidable = self.get_object()
        queryset = primary_decidable.secondary_decidables.all()
        queryset = self.filter_queryset(queryset)
        queryset = self.annotate_queryset(queryset)
        queryset = self.get_decidables_rank(
            queryset,
            queryset=primary_decidable.secondary_decidables.all()
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data,status.HTTP_200_OK)


    @aspect.mapping.post
    def create_aspect(self, request, *args, **kwargs):
        primary_decidable = self.get_object()

        parser = NestedParser(request.data)
        if not parser.is_valid():
            return Response(parser.errors,status.HTTP_200_OK)

        data = parser.validate_data
        attachments = data.pop('attachments',[])

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        group_user = GroupUser.objects.filter(
            user=request.user,
            group_id=request.data.get('group')
        ).first()
        aspect = serializer.save(
            created_by=group_user,
            primary_decidable=primary_decidable,
            root_decidable = primary_decidable.get_root_decidable()
        )

        # Add all groups that are within root decidable        
        root_decidable = primary_decidable.get_root_decidable()
        group_ids = [group.id for group in root_decidable.groups.all()]
        for group_id in group_ids:
            aspect.groups.add(group_id)

    
        # Attach all options in the primary decidable to the aspect decidable
        for option in primary_decidable.options.all():
            aspect.options.add(option)
        
            for group in aspect.get_root_decidable().groups.all():
                decidable_option = decidable_models.DecidableOption.objects.get(
                    decidable = aspect,
                    option = option
                )
                decidable_option.groups.add(group)
        
        for attachment in attachments:
            attachment['decidable'] = aspect.id

        attachment_serializer = decidable_serializers.AttachmentCreateSerializer(data=attachments,many=True)
        if attachment_serializer.is_valid():
            attachment_serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)    


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
        ).annotate(
            votes=Subquery(
                decidable_models.GroupDecidableOptionAccess.objects.filter(
                    group=self.get_group(),
                    decidable_option__option__id=OuterRef('id'),
                    decidable_option__decidable=self.get_decidable()
                ).values('value')[:1]
            ),
            user_vote=Subquery(
                decidable_models.GroupUserDecidableOptionVote.objects.filter(
                    group_decidable_option_access__group=self.get_group(),
                    group_decidable_option_access__decidable_option__option_id=OuterRef('id'),
                    group_decidable_option_access__decidable_option__decidable=self.get_decidable(),
                    group_user__group=self.get_group(),
                    group_user__user=self.request.user
                ).values('value')[:1]
            )
        )

        return queryset

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
            )
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
        queryset = self.get_options_rank(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        decidable = self.get_decidable()

        parser = NestedParser(request.data)
        if not parser.is_valid():
            return Response(parser.errors,status.HTTP_200_OK)

        data = parser.validate_data
        attachments = data.pop('attachments',[])

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        option = serializer.save(
            root_decidable=decidable.get_root_decidable()
        )
        option.decidables.add(self.get_decidable())

        # Add group
        for group in decidable.get_root_decidable().groups.all():
            decidable_option = decidable_models.DecidableOption.objects.get(
                decidable = self.get_decidable(),
                option = option
            )
            decidable_option.groups.add(group)

        # Add attachments
        for attachment in attachments:
            attachment['option'] = option.id

        
        attachment_serializer = decidable_serializers.AttachmentCreateSerializer(data=attachments,many=True)
        if attachment_serializer.is_valid():
            attachment_serializer.save()

            
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['POST']
    )
    def vote(self, request, *args, **kwargs):
        option = self.get_object()
        decidable = self.get_decidable()
        group = self.get_group()

        value = request.data.get('vote')
        if value is None:
            return Response("Vote missing",status.HTTP_400_BAD_REQUEST)
        
        decidable_option = option.decidable_option.filter(
            decidable = decidable
        ).first()
        # Get groups with access to option, that the user is a part of
        group_decidable_option_accesses = decidable_option.group_decidable_option_access.filter(
            group__groupuser__user=request.user,
            group__groupuser__active=True
        )

        # Set the user's vote for all of the above groups with the current vote
        for group_decidable_option_access in group_decidable_option_accesses:
            group_user = group_decidable_option_access.group.groupuser_set.get(
                user=request.user,
                active=True
            )
            decidable_models.GroupUserDecidableOptionVote.objects.update_or_create(
                group_decidable_option_access=group_decidable_option_access,
                group_user=group_user,
                defaults={
                    'value':request.data.get('vote')
                }
            )

        # For each group, update votes
        for group_decidable_option_access in group_decidable_option_accesses:
            group_decidable_option_access.value = group_decidable_option_access.group_user_decidable_option_vote.aggregate(Sum('value'))['value__sum'] or 0
            group_decidable_option_access.save()

        return Response("OK",status.HTTP_200_OK)