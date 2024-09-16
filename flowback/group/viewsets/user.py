
from flowback.group.models import Group
from flowback.group.models import GroupUser
from rest_framework import viewsets
import django_filters
from rest_framework.permissions import BasePermission
from flowback.group.filters import GroupUserFilter
from flowback.group.serializers import GroupUserSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from flowback.user.models import User
from flowback.group.models import GroupUserInvite
from flowback.group.fields import GroupUserInviteStatusChoices as choices
from flowback.user.serializers import BasicUserSerializer
import rules.predicates
from flowback.group import rules as group_rules
class GroupUserViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        return rules.predicates.is_authenticated(request.user)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)


class GroupUserViewSet(
    viewsets.ModelViewSet
):
    _group = None

    serializer_class = GroupUserSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = GroupUserFilter
    permission_classes = [GroupUserViewSetPermission]


    def get_queryset(self):
        return GroupUser.objects.filter(
            active=True,
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
        methods=['GET']
    )
    def me(self, request, *args, **kwargs):
        group_user = GroupUser.objects.filter(
            group = self.get_group(),
            user = request.user
        ).first()
        if not group_user:
            return Response({},status.HTTP_200_OK)
        return Response(
            GroupUserSerializer(group_user).data,
            status.HTTP_200_OK
        )
    
    @action(
        detail=False,
        methods=['GET']
    )
    def can_be_invited(self, request, *args, **kwargs):
        user = User.objects.get(id=request.GET.get('user_id'))
        
        # Check if user is already in group
        if GroupUser.objects.filter(
            group=self.get_group(),
            user=user,
            active=True
        ).exists():
            return Response(
                {
                    "flag":False,
                    "reason":"member"
                },
                status.HTTP_200_OK
            )
        # Check if user has a pending invite
        if GroupUserInvite.objects.filter(
            user=user,
            group=self.get_group(),
            status__in=[
                choices.PENDING,
            ]
        ).exists():
            return Response(
                {
                    "flag":False,
                    "reason":"pending_invite"
                },
                status.HTTP_200_OK
            )
        # User may be invited
        
        return Response(
                {
                    "flag":True,
                    "reason":"",
                    "user":BasicUserSerializer(user).data
                },
                status.HTTP_200_OK
            ) 
    
    @action(
        detail=True,
        methods=['POST'],
        url_path='remove-from-group'
    )
    def remove_from_goup(self, request, *args, **kwargs):
        group_user = self.get_object()
        # Cannot remove admin
        if group_user.is_admin:
            return Response("Cannot remove admin",status.HTTP_400_BAD_REQUEST)
        
        group_user.delete()
        return Response("OK",status.HTTP_204_NO_CONTENT)