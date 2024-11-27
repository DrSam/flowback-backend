from rest_framework import serializers
from feed.models import Message
from feed.models import Attachment
from feed.models import Channel
from feed.models import ChannelParticipant
from flowback.user.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

class ChannelSerializer(serializers.ModelSerializer):
    group = serializers.SerializerMethodField()

    def get_group(self,obj):
        from flowback.group.serializers import BasicGroupSerializer
        return BasicGroupSerializer(obj.group).data

    class Meta:
        model = Channel
        fields = "__all__"


class ChannelParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    channel = ChannelSerializer()

    class Meta:
        model = ChannelParticipant
        fields = "__all__"

class AttachmentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self,obj):
        return obj.file.name if obj.file else obj.image.name if obj.image else ''


    class Meta:
        model = Attachment
        fields = "__all__"



class ParentSerializer(serializers.ModelSerializer):
    channel_participant = ChannelParticipantSerializer(read_only=True)

    class Meta:
        model = Message
        fields = "__all__"



class MessageSerializer(serializers.ModelSerializer):
    channel_participant = ChannelParticipantSerializer(read_only=True)
    channel_participant_id = serializers.PrimaryKeyRelatedField(
        queryset = ChannelParticipant.objects,
        required=False,
        write_only=True
    )
    attachments = AttachmentSerializer(many=True,read_only=True)
    parent = ParentSerializer(read_only=True)

    class Meta:
        model = Message
        fields = "__all__"