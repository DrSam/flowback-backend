from rest_framework import serializers

from flowback.user.models import User
from flowback.user.models import PasswordReset
from flowback.user.models import OnboardUser
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','first_name','last_name', 'username','email','birth_date','profile_image', 'banner_image','language')


class OnBoardUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OnboardUser
        fields = ('username','email')
    
    def create(self, validated_data):
        if User.objects.filter(username=validated_data['username']).exists():
            raise ValidationError('Username already exists')
        if User.objects.filter(email=validated_data['email']).exists():
            raise ValidationError('Email already exists')
        
        return super().create(validated_data)
        

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardUser
        fields = ['username','email']
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        if OnboardUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email has a pending registration.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already registered.")
        if OnboardUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username has a pending registration.")
        return value
    

class UserVerifySerializer(serializers.Serializer):
    verification_code = serializers.CharField()
    password = serializers.CharField()

    def validate_password(self,value):
        if validate_password(value) is None:
            return value
    
    def validate_verification_code(self,value):
        if not OnboardUser.objects.filter(
            verification_code=value,
            is_verified=False
        ).exists():
            raise ValidationError('Verification code already used')
        return value

    
    def create(self, validated_data):
        if not validated_data['verification_code']:
            raise ValidationError('hi')
        onboard_user = OnboardUser.objects.get(
            verification_code = validated_data['verification_code']
        )

        user = User.objects.create_user(
            username = onboard_user.username,
            email = onboard_user.email,
            password = validated_data['password']
        )
        return user
    

class UserForgotPasswordSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='email'
    )

    class Meta:
        model = PasswordReset
        fields = ["user",]


class UserPasswordForgotVerifySerializer(serializers.Serializer):
    verification_code = serializers.CharField()
    password = serializers.CharField()

    def validate_password(self,value):
        if validate_password(value) is None:
            return value
    
    def validate_verification_code(self,value):
        if not PasswordReset.objects.filter(
            verification_code=value,
            is_verified=False
        ).exists():
            raise ValidationError('Verification code already used')
        return value
