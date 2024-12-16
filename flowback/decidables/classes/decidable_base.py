from feed.models import Channel
from feed.fields import ChannelTypechoices
from flowback.user.models import User
from flowback.decidables import models as decidable_models
from flowback.decidables import fields as decidable_fields
from flowback.group.models import GroupUser
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
            self.decidable.save()
            self.on_confirm()
            for group in self.decidable.groups.all():
                root_group_decidable_access = self.decidable.root_decidable.group_decidable_access.get(group=group)
                group_decidable_access = self.decidable.group_decidable_access.get(group=group)
                group_decidable_access.root_group_decidable_access = root_group_decidable_access
                group_decidable_access.state = root_group_decidable_access.state
                group_decidable_access.save()
    
    def on_confirm(self):
        raise NotImplementedError('On confirm not implemented')
    
    def create_feed_channel(self):
        for group_decidable_access in self.decidable.group_decidable_access.all():
            channel = Channel.objects.create(
                type=ChannelTypechoices.DECIDABLE,
                title=f'{self.decidable.title} Feed'
            )
            group_decidable_access.feed_channel = channel
            group_decidable_access.save()
        
            # Add Add all users in decidable groups to channel
            group_users = GroupUser.objects.filter(
                group__in=self.decidable.groups.all()
            )
            channel.participants.add(*group_users)
        
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
        )
        linkfile_poll.groups.set(list(self.decidable.get_root_decidable().groups.values_list('id',flat=True)))
        for group_decidable_access in linkfile_poll.group_decidable_access.all():
            parent_group_decidable_access = linkfile_poll.parent_decidable.group_decidable_access.get(
                group=group_decidable_access.group
            )
            group_decidable_access.state = parent_group_decidable_access.state
            group_decidable_access.save()
    
    def on_option_create(self,option):
        raise NotImplementedError('On option create not implemented')
