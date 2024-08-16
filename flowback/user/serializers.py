from rest_framework import serializers

from flowback.user.models import User
from flowback.user.models import OnboardUser
from rest_framework.exceptions import ValidationError

class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'profile_image', 'banner_image')


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