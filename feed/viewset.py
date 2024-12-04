from rest_framework.viewsets import ModelViewSet
from feed import models as feed_models
from feed import serializers as feed_serializers
from feed.models import Channel
from feed.models import ChannelParticipant
import django_filters
from rest_framework import status
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.permissions import BasePermission
from nested_multipart_parser import NestedParser
from rest_framework.decorators import action
from django.db.models import Count

class FeedViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        return super().has_permission(request,view)

    def has_object_permission(self, request, view, obj):
        if view.action == 'destroy':
            return obj.channel_participant.user == request.user
        return super().has_object_permission(request,view,obj)


class MessageViewSet(
    ModelViewSet
):
    _channel = None

    permission_classes = [FeedViewSetPermission]
    queryset = feed_models.Message.objects
    serializer_class = feed_serializers.MessageSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]

    def get_queryset(self):
        return super().get_queryset().annotate(
            likes_count = Count('likes')
        )

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
        quote_id = data.pop('quote_id',None)

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)

        message = serializer.save(channel_participant_id=channel_participant.id,parent_id=parent_id,quote_id=quote_id)
        
        for attachment in attachments:
            attachment['message'] = message.id
        
        attachment_serializer = feed_serializers.AttachmentSerializer(data=attachments,many=True)
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
                            'type':'message_created',
                            'message':serializer.data
                        }
                    }
            }
        )

        return Response(serializer.data,status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        channel = instance.channel_participant.channel

        self.perform_destroy(instance)
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
                            'type':'message_deleted',
                            'message':instance_id
                        }
                    }
            }
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def perform_update(self, serializer):
        serializer.save(is_edited=True)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        
        parser = NestedParser(request.data)
        if not parser.is_valid():
            return Response(parser.errors,status.HTTP_200_OK)
        
        data = parser.validate_data
        attachments = data.pop('attachments',[])
        old_attachment_ids = data.pop('old_attachments',[])

        channel = self.get_channel()
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        instance.attachments.exclude(id__in=old_attachment_ids).delete()

        for attachment in attachments:
            attachment['message'] = instance.id
        
        attachment_serializer = feed_serializers.AttachmentSerializer(data=attachments,many=True)
        if attachment_serializer.is_valid():
            attachment_serializer.save()

        

        serializer = feed_serializers.MessageUpdateSerializer(instance=instance)

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
                            'type':'message_updated',
                            'message':serializer.data
                        }
                    }
            }
        )

        return Response(serializer.data,status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['PATCH']
    )
    def like(self, request, *args, **kwargs):
        message = self.get_object()
        like_value = request.data.get('like')
        if like_value is True:
            message.likes.add(request.user)
        elif like_value is False:
            message.likes.remove(request.user)
        
        message = self.get_queryset().filter(id=message.id).first()
        serializer = self.get_serializer(instance=message)
        return Response(serializer.data,status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['GET']
    )
    def last_100(self,request,*args, **kwargs):
        queryset = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(instance=queryset,many=True)
        return Response(serializer.data,status.HTTP_200_OK)