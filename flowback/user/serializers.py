from rest_framework import serializers

from flowback.user.models import User


class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','first_name','last_name', 'username', 'profile_image', 'banner_image')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']