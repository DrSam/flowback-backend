from rest_framework import serializers
from feed.models import Message
from feed.models import Channel
from feed.models import ChannelParticipant
from flowback.user.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = "__all__"


class ChannelParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    channel = ChannelSerializer()

    class Meta:
        model = ChannelParticipant
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    channel_participant = ChannelParticipantSerializer(read_only=True)
    channel_participant_id = serializers.PrimaryKeyRelatedField(
        queryset = ChannelParticipant.objects,
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Message
        fields = "__all__"