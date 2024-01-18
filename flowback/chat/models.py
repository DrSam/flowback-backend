from django.db import models
from django.core.exceptions import ValidationError
import pgtrigger

from flowback.common.models import BaseModel
from flowback.files.models import FileCollection
from flowback.user.models import User
from flowback.group.models import GroupUser


class MessageChannel(BaseModel):
    origin_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, null=True, blank=True)


class MessageChannelParticipant(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(MessageChannel, on_delete=models.CASCADE)
    closed_at = models.DateTimeField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'channel')


class MessageFileCollection(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(MessageChannel, on_delete=models.CASCADE)
    file_collection = models.ForeignKey(FileCollection, on_delete=models.CASCADE)

    @property
    def attachments_upload_to(self):
        return 'message'


class Message(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(MessageChannel, on_delete=models.CASCADE)
    message = models.TextField(max_length=2000)
    attachments = models.ForeignKey(MessageFileCollection, on_delete=models.SET_NULL, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL)
    active = models.BooleanField(default=True)
