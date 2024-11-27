from rest_framework.viewsets import ModelViewSet
from feed import models as feed_models
from feed import serializers as feed_serializes
from feed.models import Channel
from feed.models import ChannelParticipant
import django_filters
from rest_framework import status
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.permissions import BasePermission
from nested_multipart_parser import NestedParser


class FeedViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        return super().has_permission(request,view)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request,view,obj)


class MessageViewSet(
    ModelViewSet
):
    _channel = None

    permission_classes = [FeedViewSetPermission]
    queryset = feed_models.Message.objects
    serializer_class = feed_serializes.MessageSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]

    def get_channel(self):
        if self._channel:
            return self._channel
        
        channel_id = self.kwargs.get('channel_id')
        channel = Channel.objects.get(id=channel_id)
        self._channel = channel
        return self._channel

    def get_channel_participant(self):
        channel = self.get_channel()
        user = self.request.user

        channel_participant = ChannelParticipant.objects.filter(
            channel=channel,
            user=user,
            active=True
        ).first()

        return channel_participant

    def create(self, request, *args, **kwargs):
        parser = NestedParser(request.data)
        if not parser.is_valid():
            return Response(parser.errors,status.HTTP_200_OK)
        
        data = parser.validate_data
        attachments = data.pop('attachments',[])
        

        channel = self.get_channel()
        channel_participant = self.get_channel_participant()
        parent_id = data.pop('parent_id',None)

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)

        message = serializer.save(channel_participant_id=channel_participant.id,parent_id=parent_id)
        
        for attachment in attachments:
            attachment['message'] = message.id
        
        attachment_serializer = feed_serializes.AttachmentSerializer(data=attachments,many=True)
        if attachment_serializer.is_valid():
            attachment_serializer.save()

        # Send notification to others
        channel_layer = get_channel_layer()
        async_to_sync(
            channel_layer.group_send
        )(
            f'{channel.id}',
            {
                'type':'send_stuff',
                'data':{
                        'type':'message',
                        'data':{
                            'type':'received_message',
                            'message':serializer.data
                        }
                    }
            }
        )

        return Response(serializer.data,status.HTTP_200_OK)