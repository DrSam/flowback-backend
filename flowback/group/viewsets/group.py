
from flowback.group.models import Group
from flowback.group.models import GroupUser
from rest_framework import viewsets
from rest_framework import status
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from flowback.group.serializers import GroupSerializer
from flowback.group.serializers import GroupCreateSerializer
import django_filters
from flowback.group.filters import GroupFilter
from rest_framework.permissions import BasePermission
from flowback.group.models import GroupUserInvite
from flowback.group.fields import GroupUserInviteStatusChoices
from flowback.group.serializers import GroupUserInviteSerializer
import rules.predicates
from feed.models import Channel
from feed.fields import ChannelTypechoices
from flowback.group import rules as group_rules
from django.db.models import Q
from django.db.models import Subquery, OuterRef, Count
from flowback.user.models import User
from django_q.tasks import async_task
from flowback.group.tasks import share_group_with_user
from flowback.group.tasks import share_group_with_email
from flowback.group.utils import add_user_to_group
import re

def is_valid_email(email):
    if not isinstance(email,str):
        return False
    # Regular expression for validating an email
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None


class GroupViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        return rules.predicates.is_authenticated(request.user)

    def has_object_permission(self, request, view, obj):
        if view.action == 'can_update':
            return group_rules.is_admin.test(request.user,obj)
        if view.action == 'update':
            return group_rules.is_group_admin.test(request.user,obj)
        return super().has_object_permission(request,view,obj)


class GroupViewSet(
    viewsets.ModelViewSet
):
    queryset = Group.objects
    serializer_class = GroupSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = GroupFilter
    permission_classes = [GroupViewSetPermission]

    def get_serializer_class(self):
        if self.action == 'invites':
            return GroupUserInviteSerializer
        elif self.action == 'create':
            return GroupCreateSerializer
        return super().get_serializer_class()
    
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == 'list':
            queryset = queryset.filter(
                public=True
            ).exclude(
                group_users__user=self.request.user
            )
        queryset = queryset.annotate(
            member_count = Count('group_users',distinct=True),
            admin_count = Count('group_users',filter=Q(group_users__is_admin=True),distinct=True),
            open_poll_count = Count('decidables',filter=Q(decidables__state='open'),distinct=True),
            is_member = Subquery(
                GroupUser.objects.filter(
                    user=self.request.user,
                    group_id=OuterRef('id'),
                    active=True
                ).values('id')[:1]
            ),
            is_admin = Subquery(
                GroupUser.objects.filter(
                    user=self.request.user,
                    group_id=OuterRef('id'),
                    active=True,
                    is_admin=True
                ).values('id')[:1]
            ),
            is_pending_invite=Subquery(
                GroupUserInvite.objects.filter(
                    user=self.request.user,
                    group_id=OuterRef('id'),
                    status=GroupUserInviteStatusChoices.PENDING,
                    external=False
                ).values('id')[:1]
            ),
            is_pending_join_request=Subquery(
                GroupUserInvite.objects.filter(
                    user=self.request.user,
                    group_id=OuterRef('id'),
                    status=GroupUserInviteStatusChoices.PENDING,
                    external=True
                ).values('id')[:1]
            )
        )
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        data['description'] = data['description'].replace('\r\n','\n')
        data['long_description'] = data['long_description'].replace('\r\n','\n')

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)
        
        group = serializer.save(created_by=request.user)

        group_user = GroupUser.objects.create(
            group=group,
            user=request.user,
            is_admin=True
        )

        channel = Channel.objects.create(
            type = ChannelTypechoices.GROUP,
            title = group.name,
        )
        group.feed_channel = channel
        group.save()

        channel.participants.add(group_user)

        return Response("OK",status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'description' in data:
            data['description'] = data['description'].replace('\r\n','\n')
        if 'long_description' in data:
            data['long_description'] = data['long_description'].replace('\r\n','\n')

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @action(
        detail=True,
        methods=['GET'],
        url_path='can-update'
    )
    def can_update(self, request, *args, **kwargs):
        object = self.get_object()
        return Response("OK",status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['GET']
    )
    def invites(self, request, *args, **kwargs):
        user_invites = GroupUserInvite.objects.filter(
            status = GroupUserInviteStatusChoices.PENDING,
            user=request.user
        )
        serializer = self.get_serializer(user_invites,many=True)
        return Response(serializer.data,status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['GET'],
        url_path='my'
    )
    def my_groups(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        if request.GET.get('is_admin'):
            queryset = queryset.filter(
                group_users__user=request.user,
                group_users__is_admin=True
            )
        else:
            queryset = queryset.filter(
                group_users__user=request.user
            )
        
        serializer = self.get_serializer(instance=queryset,many=True)
        return Response(serializer.data,status.HTTP_200_OK)
    
    @action(
        detail=True,
        methods=['POST']
    )
    def share(self, request, *args, **kwargs):
        group = self.get_object()

        # split IDs and emails
        ids = [id for id in request.data.get('user_ids') if isinstance(id,int)]
        emails = [email for email in request.data.get('user_ids') if is_valid_email(email)]

        users = User.objects.filter(
            id__in=ids
        )
        for user in users:
            share_group_with_user(
                group.id,
                user.id,
                request.user.id
            )
        
        for email in emails:
            share_group_with_email(
                group.id,
                email,
                request.user.id
            )
        
          
        return Response("OK",status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['POST']
    )
    def join(self, request, *args, **kwargs):
        group = self.get_object()
        user = request.user
        if not group.direct_join:
            return Response("Need an invitation",status.HTTP_401_UNAUTHORIZED)
        
        add_user_to_group(group,user)

        return Response("OK",status.HTTP_200_OK)


