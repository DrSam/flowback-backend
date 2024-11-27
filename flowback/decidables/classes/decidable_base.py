from feed.models import Channel
from feed.fields import ChannelTypechoices
from flowback.user.models import User
from flowback.decidables import models as decidable_models
from flowback.decidables import fields as decidable_fields

class BaseDecidable:
    decidable_type = None
    decidable = None

    def __init__(self,decidable,user=None,group=None):
        self.decidable = decidable
        self.user = user
        self.group = group

    def on_create(self):
        if self.decidable.primary_decidable:
            self.decidable.root_decidable = self.decidable.primary_decidable.get_root_decidable()
            self.decidable.save()
        elif self.decidable.parent_decidable:
            self.decidable.root_decidable = self.decidable.parent_decidable.get_root_decidable()
            self.decidable.save()
        elif self.decidable.parent_option:
            self.decidable.root_decidable = self.decidable.parent_option.root_decidable
            self.decidable.save()
        
        if self.decidable.root_decidable:
            self.decidable.confirmed = self.decidable.root_decidable.confirmed
            self.decidable.state = self.decidable.root_decidable.state
            self.decidable.save()
    
    def on_confirm(self):
        raise NotImplementedError('On confirm not implemented')
    
    def create_feed_channel(self):
        channel = Channel.objects.create(
            type=ChannelTypechoices.DECIDABLE,
            title=f'{self.decidable.title} Feed',
            decidable=self.decidable
        )
        
        # Add Add all users in decidable groups to channel
        users = list(
            User.objects.filter(
                groupuser__group__in=self.decidable.groups.all()
            )
        )
        channel.participants.add(*users)
    
    def create_linkfile_poll(self):
        linkfile_poll = decidable_models.Decidable.objects.create(
            title = f'linkfile poll for {self.decidable.title}',
            root_decidable = self.decidable.get_root_decidable(),
            parent_decidable = self.decidable,
            created_by = self.decidable.created_by,
            decidable_type=decidable_fields.DecidableTypeChoices.LINKFILEPOLL,
            voting_type=decidable_fields.VoteTypeChoices.APPROVAL,
            members_can_add_options=True,
            confirmed=True,
            state=self.decidable.get_root_decidable().state
        )
        linkfile_poll.groups.set(list(self.decidable.get_root_decidable().groups.values_list('id',flat=True)))
    
    def on_option_create(self,option):
        raise NotImplementedError('On option create not implemented')
