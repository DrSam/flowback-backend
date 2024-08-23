from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins
from rest_framework.permissions import BasePermission
import django_filters
from flowback.group.models import GroupUserInvite
from flowback.group.models import Group
from flowback.group.serializers import GroupUserInviteSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from flowback.user.models import User
from flowback.group.fields import GroupUserInviteStatusChoices
from flowback.group.models import GroupUser


class GroupUserInvitationViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)


class GroupUserInvitationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    _group = None

    serializer_class = GroupUserInviteSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = None
    permission_classes = [GroupUserInvitationViewSetPermission]

    def get_queryset(self):
        return GroupUserInvite.objects.filter(
            group=self.get_group()
        )
    
    def get_group(self):
        if self._group:
            return self._group
        
        group_id = self.kwargs.get('group_id')
        group = Group.objects.get(id=group_id)
        self._group = group
        return self._group
    
    @action(
        detail=False,
        methods=['POST']
    )
    def send_invite(self, request, *args, **kwargs):
        group = self.get_group()

        users = User.objects.filter(
            id__in=request.data.get('user_ids',[])
        ).exclude(
            groupuserinvite__group=group,
            groupuserinvite__status=GroupUserInviteStatusChoices.PENDING
        ).exclude(
            groupuser__group=group,
            groupuser__active=True
        )
        for user in users:
            GroupUserInvite.objects.create(
                user=user,
                group=group,
                external=False
            )
        return Response("OK",status.HTTP_200_OK)
    
    @action(
        detail=True,
        methods=['POST']
    )
    def accept_invite(self, request, *args, **kwargs):
        # TODO: Admin or users with invite_user permission can also accept invitations
        # For now, only invited user accepts
        group_invite = self.get_object()
        # Check permission
        if request.user != group_invite.user:
            return Response("Only invited user may accept invitation",status.HTTP_403_FORBIDDEN)
        # Check if user group already exists:
        if GroupUser.objects.filter(
            group=self.get_group(),
            user=group_invite.user
        ).exists():
            group_invite.status = GroupUserInviteStatusChoices.WITHDRAWN
            group_invite.save()
            return Response("User already member of group",status.HTTP_403_FORBIDDEN)
        
        # Accept invitation
        group_invite.status = GroupUserInviteStatusChoices.ACCEPTED
        group_invite.save()
        GroupUser.objects.create(
            group=group_invite.group,
            user=group_invite.user
        )
        return Response("OK",status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['POST']
    )
    def reject_invite(self, request, *args, **kwargs):
        # TODO: Admin or users with invite_user permission can also reject invitations
        # For now, only invited user accepts
        group_invite = self.get_object()
        # Check permission
        if request.user != group_invite.user:
            return Response("Only invited user may reject invitation",status.HTTP_403_FORBIDDEN)
        # Check if user group already exists:
        if GroupUser.objects.filter(
            group=self.get_group(),
            user=group_invite.user
        ).exists():
            group_invite.status = GroupUserInviteStatusChoices.WITHDRAWN
            group_invite.save()
            return Response("User already member of group",status.HTTP_403_FORBIDDEN)
        
        # Reject invitation
        group_invite.status = GroupUserInviteStatusChoices.REJECTED
        group_invite.save()
        return Response("OK",status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['POST']
    )
    def withdraw_invite(self, request, *args, **kwargs):
        # TODO: Admin or users with invite_user permission can also reject invitations
        group_invite = self.get_object()
        # Check permission
        if request.user == group_invite.user:
            return Response("Withdrawal is for admin, user may reject invitation",status.HTTP_403_FORBIDDEN)        
        
        # Withdraw invitation
        group_invite.status = GroupUserInviteStatusChoices.WITHDRAWN
        group_invite.save()
        return Response("OK",status.HTTP_200_OK)