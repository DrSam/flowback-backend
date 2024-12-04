from django.contrib import admin
from feed.models import Channel
from feed.models import ChannelParticipant
from feed.models import Message

# Register your models here.
admin.site.register(Channel)
admin.site.register(ChannelParticipant)
admin.site.register(Message)
