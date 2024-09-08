from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from flowback.user.serializers import UserSerializer
from flowback.user.serializers import BasicUserSerializer
from flowback.user.serializers import UserRegisterSerializer
from flowback.user.serializers import UserVerifySerializer
from flowback.user.serializers import UserForgotPasswordSerializer
from flowback.user.serializers import UserPasswordForgotVerifySerializer
from flowback.user.serializers import UserProfileSerializer
from flowback.user.models import  User
from flowback.user.models import  PasswordReset
from django.contrib.auth.password_validation import validate_password
import django_filters.rest_framework
from flowback.user.filters import UserFilter
from backend.settings import DEFAULT_FROM_EMAIL, FLOWBACK_URL
from django.core.mail import send_mail
from rest_framework.permissions import BasePermission
import rules
from django.contrib.auth.password_validation import validate_password
from flowback.user.fields import LanguageOptions

class UserViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action in ['register','register_verify','forgot','forgot_verify']:
            return True
        return rules.predicates.is_authenticated(request.user)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request,view, obj)


class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = User.objects
    serializer_class = BasicUserSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = UserFilter
    permission_classes = [UserViewSetPermission]

    def get_serializer_class(self):
        if self.action in ['profile','update_profile']:
            return UserProfileSerializer
        if self.action == 'register':
            return UserRegisterSerializer
        elif self.action == 'register_verify':
            return UserVerifySerializer
        elif self.action == 'forgot':
            return UserForgotPasswordSerializer
        elif self.action == 'forgot_verify':
            return UserPasswordForgotVerifySerializer
        return super().get_serializer_class()

    @action(
        detail=False,
        methods=['GET']
    )
    def me(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(instance=user)
        return Response(serializer.data,status.HTTP_200_OK)

    @me.mapping.patch
    def set_me(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(instance=user,data=request.data,partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data,status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def change_password(self, request, *args, **kwargs):
        user = request.user
        print(request.data)
        # Verify user by checking old password
        if not user.check_password(request.data.get('currentPassword')):
            return Response(
                {
                    'detail':'curr_pass_incorrect'
                },
                status.HTTP_400_BAD_REQUEST
            )
        # Validate new password
        validate_password(request.data.get('newPassword'))

        # Save new password
        user.set_password(request.data.get('newPassword'))
        user.save()
        return Response("OK",status.HTTP_200_OK)
    
    @action(
        detail=False,
        methods=['GET'],
        url_path='blocked-users'
    )
    def blocked_users(self, request, *args, **kwargs):
        blocked_users = request.user.blocked_users.all()
        serializer = self.get_serializer(instance=blocked_users,many=True)
        return Response(serializer.data,status.HTTP_200_OK)
        
    @action(
        detail=False,
        methods=['POST'],
        url_path='block-user'
    )
    def block(self, request, *args, **kwargs):
        user = request.user
        to_block_id = request.data.get('user_id')
        user_to_block = User.objects.get(id=to_block_id)
        user.blocked_users.add(user_to_block)
        return Response("OK",status.HTTP_200_OK)
    
    @action(
        detail=False,
        methods=['POST'],
        url_path='unblock-user'
    )
    def unblock(self, request, *args, **kwargs):
        user = request.user
        to_unblock_id = request.data.get('user_id')
        user_to_unblock = User.objects.get(id=to_unblock_id)
        user.blocked_users.remove(user_to_unblock)
        return Response("OK",status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['POST']
    )
    def register(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()

        link = f'Use this code to create your account: {user.verification_code}'
        if FLOWBACK_URL:
            link = f'''Use this link to create your account: {FLOWBACK_URL}/create_account/
                    ?email={user.email}&verification_code={user.verification_code}'''

        send_mail('Flowback Verification Code', link, DEFAULT_FROM_EMAIL, [user.email])

        return Response("OK",status.HTTP_200_OK)
    
    @action(
        detail=False,
        methods=['POST'],
        url_path='register/verify'
    )
    def register_verify(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response("OK",status.HTTP_201_CREATED)
    

    @action(
        detail=False,
        methods=['POST']
    )
    def forgot(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response("OK",status.HTTP_200_OK)
        
        reset = serializer.save()
        user = reset.user
        
        password_reset = PasswordReset.objects.create(user=user)

        link = f'Use this code to reset your account password: {password_reset.verification_code}'

        if FLOWBACK_URL:
            link = f'''Use this link to reset your account password: {FLOWBACK_URL}/forgot_password/
                        ?email={user.email}&verification_code={password_reset.verification_code}'''

        send_mail('Flowback Verification Code', link, DEFAULT_FROM_EMAIL, [user.email])
        return Response("OK",status.HTTP_200_OK)
    

    @action(
        detail=False,
        methods=['POST'],
        url_path='forgot/verify'
    )
    def forgot_verify(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(
            passwordreset__verification_code=serializer.validated_data['verification_code']
        )
        user.set_password(serializer.validated_data['password'])
        user.save()
        return Response("OK",status.HTTP_200_OK)
        

    @action(
        detail=False,
        methods=['GET'],
        url_path='(?P<username>[^/.]+)/profile'
    )
    def profile(self, request, *args, **kwargs):
        user = User.objects.filter(username=kwargs.get('username')).first()
        if not user:
            return Response("User not found",status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(instance=user)
        return Response(serializer.data,status.HTTP_200_OK)
    
    
    @profile.mapping.patch
    def update_profile(self, request, *args, **kwargs):
        user = User.objects.filter(username=kwargs.get('username')).first()
        if user!=request.user:
            return Response("Not allowed",status.HTTP_401_UNAUTHORIZED)
        
        if 'profile_image' in request.FILES or 'banner_image' in request.FILES:
            serializer = self.get_serializer(instance=user,data=request.data,partial=True)
        else:
            data = request.data.copy()
            data.pop('profile_image')
            data.pop('banner_image')
            serializer = self.get_serializer(instance=user,data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            serializer = self.get_serializer(instance=user)
            return Response(serializer.data,status.HTTP_200_OK)
        return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)


