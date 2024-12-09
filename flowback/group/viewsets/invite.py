from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework.permissions import BasePermission
import django_filters
from flowback.group.models import GroupUserInvite
from flowback.group.models import Group
from flowback.group.serializers import GroupUserInviteSerializer
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from flowback.user.models import User
from flowback.group.fields import GroupUserInviteStatusChoices
from flowback.group.models import GroupUser
from flowback.group.filters import GroupUserInviteFilter
from flowback.group import rules as group_rules
import rules.predicates
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from feed.models import Channel
from feed.fields import ChannelTypechoices
from django.db.models import Q
from flowback.group.utils import add_user_to_group
from flowback.group.tasks import invite_user_to_group
from flowback.group.tasks import invite_email_to_group
import re

def is_valid_email(email):
    if not isinstance(email,str):
        return False
    # Regular expression for validating an email
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None


class GroupUserInvitationViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action in ['send_invite','withdraw_invite','accept_request','reject_request']:
            return group_rules.is_group_admin.test(request.user,view.get_group())
        
        return rules.predicates.is_authenticated.test(request.user)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)


class GroupUserInvitationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    _group = None
    _group_user = None

    serializer_class = GroupUserInviteSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = GroupUserInviteFilter
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
    
    def get_group_user(self):
        if not self._group_user and self.request.user.is_authenticated:
            group_user = GroupUser.objects.filter(
                group=self.get_group(),
                user=self.request.user
            ).first()
            self._group_user = group_user
        
        return self._group_user

    @action(
        detail=False,
        methods=['POST'],
        url_path='send-invite'
    )
    def send_invite(self, request, *args, **kwargs):
        group = self.get_group()

        # split IDs and emails
        ids = [id for id in request.data.get('user_ids') if isinstance(id,int)]
        emails = [email for email in request.data.get('user_ids') if is_valid_email(email)]

        # Send invites for users
        users = User.objects.filter(
            id__in=ids
        ).exclude(
            groupuserinvite__group=group,
            groupuserinvite__status=GroupUserInviteStatusChoices.PENDING
        ).exclude(
            group_users__group=group,
            group_users__active=True
        )
        for user in users:
            GroupUserInvite.objects.create(
                user=user,
                group=group,
                external=False,
                initiator=request.user
            )
            # Send email for invited users
            invite_user_to_group(group.id,user.id,request.user.id)
        

        # Create invites for non-users
        for email in emails:
            GroupUserInvite.objects.create(
                email=email,
                group=group,
                external=False,
                initiator=request.user
            )
            # Send email for invited users
            invite_email_to_group(group.id,email,request.user.id)

        # Send notification to invited person
        channel_layer = get_channel_layer()
        for user_id in ids:
            async_to_sync(
                channel_layer.group_send
            )(
                f'user_{user_id}',
                {
                    'type':'send_stuff',
                    'data':{
                        'type':'notification',
                        'data':{
                            'type':'send_invite',
                            'group_name':group.name,
                            'group_id':group.id,
                            'initiator':request.user.get_full_name()
                        }
                    }
                }
            )
        

        return Response("OK",status.HTTP_200_OK)
    
    @action(
        detail=False,
        methods=['POST'],
        url_path='accept-invite'
    )
    def accept_invite(self, request, *args, **kwargs):
        group = self.get_group()

        group_invite = GroupUserInvite.objects.filter(
            group=self.get_group(),
            user=request.user,
            status=GroupUserInviteStatusChoices.PENDING,
            external=False,
        ).first()
        if not group_invite:
            return Response("No invite exists",status.HTTP_400_BAD_REQUEST)
        
        # Accept invitation
        group_invite.status = GroupUserInviteStatusChoices.ACCEPTED
        group_invite.save()
    
        add_user_to_group(group_invite.group,group_invite.user)
        
        return Response("OK",status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['POST'],
        url_path='reject-invite'
    )
    def reject_invite(self, request, *args, **kwargs):
        group = self.get_group()
        group_invite = GroupUserInvite.objects.filter(
            group=self.get_group(),
            user=request.user,
            status=GroupUserInviteStatusChoices.PENDING,
            external=False
        ).first()
        # Check if invitation exists
        if not group_invite:
            return Response("No invite exists",status.HTTP_400_BAD_REQUEST)
        
        # Reject invitation
        group_invite.status = GroupUserInviteStatusChoices.REJECTED
        group_invite.save()

        if not group_invite.initiator:
            print('no initiator found')
            return Response("OK",status.HTTP_200_OK)

        channel_layer = get_channel_layer()
        async_to_sync(
            channel_layer.group_send
        )(
            f'user_{group_invite.initiator.id}',
            {
                'type':'send_stuff',
                'data':{
                    'type':'notification',
                    'data':{
                        'type':'reject_invite',
                        'group_name':group.name,
                        'group_id':group.id,
                        'user_id':group_invite.user.id,
                        'user_name':group_invite.user.get_full_name()
                    }
                }
            }
        )

        return Response("OK",status.HTTP_200_OK)


    @action(
        detail=True,
        methods=['POST'],
        url_path='withdraw-invite'
    )
    def withdraw_invite(self, request, *args, **kwargs):
        group = self.get_group()
        group_invite = self.get_object()
        
        if group_invite.status!=GroupUserInviteStatusChoices.PENDING:
            return Response("Invalid invitation",status.HTTP_400_BAD_REQUEST)
        
        # Withdraw invitation
        group_invite.status = GroupUserInviteStatusChoices.WITHDRAWN
        group_invite.save()

        channel_layer = get_channel_layer()
        async_to_sync(
            channel_layer.group_send
        )(
            f'user_{group_invite.user.id}',
            {
                'type':'send_stuff',
                'data':{
                    'type':'notification',
                    'data':{
                        'type':'withdraw_invite',
                        'group_name':group.name,
                        'group_id':group.id,
                        'initiator':request.user.get_full_name()
                    }
                }
            }
        )
        return Response("OK",status.HTTP_200_OK)
    
    @action(
        detail=False,
        methods=['POST'],
        url_path='request-join'
    )
    def request_join(self, request, *args, **kwargs):
        group = self.get_group()

        # Check if user already has an existing join request
        if GroupUserInvite.objects.filter(
            user=request.user,
            group=group,
            status=GroupUserInviteStatusChoices.PENDING
        ).exists():
            return Response("Pending invite/request",status.HTTP_400_BAD_REQUEST)
        
        # Make sure user is not already part of group
        if GroupUser.objects.filter(
            user=request.user,
            group=group
        ).exists():
            return Response("User already part of group",status.HTTP_400_BAD_REQUEST)
        # Make sure group is visible
        if not group.public:
            return Response("Group is not public",status.HTTP_401_UNAUTHORIZED)
        
        GroupUserInvite.objects.create(
            user=request.user,
            group=group,
            external=True,
        )
        return Response("OK",status.HTTP_200_OK)
        
    @action(
        detail=True,
        methods=['POST'],
        url_path='accept-request'
    )
    def accept_request(self, request, *args, **kwargs):
        invite = self.get_object()

        # If invite is not pending, raise error
        if not invite.status==GroupUserInviteStatusChoices.PENDING:
            return Response("No pending invite",status.HTTP_400_BAD_REQUEST)
        
        invite.status = GroupUserInviteStatusChoices.ACCEPTED
        invite.save()

        add_user_to_group(invite.group,invite.user)

        return Response("OK",status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['POST'],
        url_path='reject-request'
    )
    def reject_request(self, request, *args, **kwarg):
        invite = self.get_object()

        # If invite is not pending, raise error
        if not invite.status==GroupUserInviteStatusChoices.PENDING:
            return Response("No pending invite",status.HTTP_400_BAD_REQUEST)
        
        invite.status = GroupUserInviteStatusChoices.REJECTED
        invite.save()
        
        return Response("OK",status.HTTP_200_OK)


@api_view(http_method_names=['GET'])
@permission_classes([IsAuthenticated])
def my_invites(request):
    group_invites = GroupUserInvite.objects.filter(
        user=request.user,
        status=GroupUserInviteStatusChoices.PENDING,
        external=False,
    )
    print(group_invites)
    serializer = GroupUserInviteSerializer(group_invites,many=True)
    return Response(serializer.data,status.HTTP_200_OK)