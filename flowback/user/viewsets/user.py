from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from flowback.user.serializers import UserSerializer
from flowback.user.serializers import BasicUserSerializer
from flowback.user.models import  User
from django.contrib.auth.password_validation import validate_password
import django_filters.rest_framework
from flowback.user.filters import UserFilter



#TODO: Add mixins or update to modelviewset as required
class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = User.objects
    serializer_class = BasicUserSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = UserFilter

    @action(
        detail=False,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def change_password(self, request, *args, **kwargs):
        user = request.user

        # Verify user by checking old password
        if not user.check_password(request.data.get('current_password')):
            return Response(
                {
                    'detail':'Current password incorrect'
                },
                status.HTTP_400_BAD_REQUEST
            )
        # Validate new password
        validate_password(request.data.get('new_password'))

        # Save new password
        user.set_password(request.data.get('new_password'))
        user.save()
        return Response("OK",status.HTTP_200_OK)
    
    @action(
        detail=False,
        methods=['GET']
    )
    def blocked_users(self, request, *args, **kwargs):
        blocked_users = request.user.blocked_users.all()
        serializer = self.get_serializer(users=blocked_users,many=True)
        return Response(serializer.data,status.HTTP_200_OK)
        
    @action(
        detail=False,
        methods=['POST']
    )
    def block(self, request, *args, **kwargs):
        user = request.user
        to_block_id = request.data.get('user_id')
        user_to_block = User.objects.get(id=to_block_id)
        user.blocked_users.add(user_to_block)
        return Response("OK",status.HTTP_200_OK)
    
    @action(
        detail=False,
        methods=['POST']
    )
    def unblock(self, request, *args, **kwargs):
        user = request.user
        to_unblock_id = request.data.get('user_id')
        user_to_unblock = User.objects.get(id=to_unblock_id)
        user.blocked_users.remove(user_to_unblock)
        return Response("OK",status.HTTP_200_OK)
