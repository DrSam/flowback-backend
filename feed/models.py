from django.db import models
from django.db.models import Q

import pgtrigger
from tree_queries.models import TreeNode

from flowback.common.models import BaseModel
from flowback.user.models import User
from feed.fields import ChannelTypechoices
from .fields import AttachmentChoices
from flowback.decidables.validators import allowed_image_extensions


class Channel(BaseModel):
    title = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=64, choices=ChannelTypechoices.choices)

    participants = models.ManyToManyField(
        'group.GroupUser',
        related_name='feed_channels',
        through='feed.ChannelParticipant'
    )

    # TODO: Triggers can be used to limit what decidables and options can have channels
    
    def __str__(self):
        return self.title
    

class ChannelParticipant(BaseModel):
    group_user = models.ForeignKey(
        'group.GroupUser',
        related_name='feed_channel_participants',
        on_delete=models.CASCADE
    )
    channel = models.ForeignKey(
        Channel,
        related_name='feed_channel_participants',
        on_delete=models.CASCADE
    )
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.channel} - {self.group_user.user.get_full_name()}'



class Message(BaseModel, TreeNode):
    channel_participant = models.ForeignKey(
        ChannelParticipant, 
        related_name='feed_messages',
        on_delete=models.CASCADE
    )
    quote = models.ForeignKey(
        'self',
        related_name='quoted_by',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    content = models.TextField(max_length=2000,blank=True,default='')

    likes = models.ManyToManyField(
        User,
        related_name='liked_messages',
        blank=True
    )
    uuid = models.CharField(max_length=16,blank=True,default='')

    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']


class Attachment(models.Model):
    type = models.CharField(
        choices=AttachmentChoices.choices,
        max_length=16
    )
    
    message = models.ForeignKey(
        'feed.Message',
        related_name='attachments',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    link = models.CharField(max_length=512,blank=True,default='')
    file = models.FileField(null=True,blank=True)
    image = models.ImageField(null=True,blank=True, validators=[allowed_image_extensions])
