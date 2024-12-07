
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
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)
        
        group = serializer.save(created_by=request.user)

        GroupUser.objects.create(
            group=group,
            user=request.user,
            is_admin=True
        )

        channel = Channel.objects.create(
            type = ChannelTypechoices.GROUP,
            title = group.name,
            group=group
        )
        channel.participants.add(request.user)

        return Response("OK",status.HTTP_201_CREATED)

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

        users = User.objects.filter(
            id__in=request.data.get('user_ids',[])
        )
        
        for user in users:
            task_id = share_group_with_user(
                group.id,
                user.id,
                request.user.id
            )

            
        return Response("OK",status.HTTP_200_OK)

