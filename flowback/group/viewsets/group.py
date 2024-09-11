
from flowback.group.models import Group
from flowback.group.models import GroupUser
from rest_framework import viewsets
from rest_framework import status
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from flowback.group.serializers import GroupSerializer
from flowback.group.serializers import GroupCreateSerializer
from flowback.group.serializers import MyGroupWithUserSerializer
import django_filters
from flowback.group.filters import GroupFilter
from rest_framework.permissions import BasePermission
from flowback.group.models import GroupUserInvite
from flowback.group.fields import GroupUserInviteStatusChoices
from flowback.group.serializers import GroupUserInviteSerializer
import rules.predicates
from flowback.chat.models import MessageChannel
from flowback.chat.models import MessageChannelParticipant
from flowback.group import rules as group_rules


class GroupViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        return rules.predicates.is_authenticated(request.user)

    def has_object_permission(self, request, view, obj):
        if view.action == 'can_update':
            return group_rules.is_admin.test(request.user,obj)
        return super().has_object_permission(request,view,obj)


class GroupViewSet(
    viewsets.ModelViewSet
):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = GroupFilter
    permission_classes = [GroupViewSetPermission]

    def get_serializer_class(self):
        if self.action == 'invites':
            return GroupUserInviteSerializer
        elif self.action == 'my_groups':
            return MyGroupWithUserSerializer
        elif self.action == 'create':
            return GroupCreateSerializer
        return super().get_serializer_class()
    
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

        message_channel = MessageChannel.objects.create(
            origin_name = 'group',
            title = group.name
        )
        group.chat = message_channel
        group.save()

        MessageChannelParticipant.objects.create(
            channel=message_channel,
            user=request.user
        )

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
        groups = Group.objects.filter(
            groupuser__user=request.user
        )
        serializer = self.get_serializer(instance=groups,many=True)
        return Response(serializer.data,status.HTTP_200_OK)