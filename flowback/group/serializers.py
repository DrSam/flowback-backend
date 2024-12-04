from rest_framework import serializers

from flowback.group.models import Group, GroupUser, GroupUserInvite
from flowback.user.serializers import BasicUserSerializer
from flowback.chat.models import MessageChannel

class BasicGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name', 'image', 'cover_image', 'hide_poll_users')


class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name','description','public','direct_join','default_quorum','default_approval_minimum','default_finalization_period']
    


class BasicGroupUserSerializer(serializers.ModelSerializer):
    user = BasicUserSerializer(required=False)
    
    class Meta:
        model = GroupUser
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):
    is_member = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    is_pending_invite = serializers.SerializerMethodField()
    is_pending_join_request = serializers.SerializerMethodField()
    member_count = serializers.IntegerField()
    admin_count = serializers.IntegerField()
    open_poll_count = serializers.IntegerField()
    feed_channels = serializers.SerializerMethodField()

    def get_feed_channels(self,obj):
        channels = obj.feed_channels.all()
        return channels.values()

    def get_is_member(self,obj):
        if bool(getattr(obj,'is_member',False)):
            return True
        return False
    
    def get_is_admin(self,obj):
        if bool(getattr(obj,'is_admin',False)):
            return True
        return False
    
    def get_is_pending_invite(self,obj):
        if bool(getattr(obj,'is_pending_invite',False)):
            return True
        return False
    
    def get_is_pending_join_request(self,obj):
        if bool(getattr(obj,'is_pending_join_request',False)):
            return True
        return False
    


    class Meta:
        model = Group
        fields = "__all__"


class GroupUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    user = BasicUserSerializer(required=False)
    is_admin = serializers.BooleanField(required=False)
    active = serializers.BooleanField(required=False)

    permission_id = serializers.IntegerField(required=False, allow_null=True)
    permission_name = serializers.CharField(required=False, source='permission.role_name', default='Member')
    group_id = serializers.IntegerField(required=False)
    group_name = serializers.CharField(required=False, source='group.name')
    group_image = serializers.CharField(required=False, source='group.image')


class GroupUserModelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    user = BasicUserSerializer(required=False)
    is_admin = serializers.BooleanField(required=False)
    active = serializers.BooleanField(required=False)

    permission_id = serializers.IntegerField(required=False, allow_null=True)
    permission_name = serializers.CharField(required=False, source='permission.role_name', default='Member')
    group_id = serializers.IntegerField(required=False)
    group_name = serializers.CharField(required=False, source='group.name')
    group_image = serializers.CharField(required=False, source='group.image')


    class Meta:
        model = GroupUser
        fields = "__all__"


class GroupUserInviteSerializer(serializers.ModelSerializer):
    user = BasicUserSerializer(read_only=True)
    group = BasicGroupSerializer(read_only=True)

    class Meta:
        model = GroupUserInvite
        fields = "__all__"
