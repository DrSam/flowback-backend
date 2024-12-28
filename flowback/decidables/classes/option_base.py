from flowback.decidables import models as decidable_models
from flowback.decidables import fields as decidable_fields
from feed.models import Channel
from feed.fields import ChannelTypechoices
from flowback.user.models import User
from flowback.group.models import GroupUser

class BaseOption:
    option = None
    decidable = None
    
    def __init__(self,option,decidable):
        self.option = option
        self.decidable = decidable


    def create_reason_poll(self):
        title = f'Reason poll for {self.option.title}'
        if len(title)>120:
            title = title[:117]+'...'
        reason_poll = decidable_models.Decidable.objects.create(
            title = title,
            root_decidable = self.decidable.get_root_decidable(),
            parent_option = self.option,
            created_by = self.decidable.created_by,
            decidable_type=decidable_fields.DecidableTypeChoices.REASONPOLL,
            voting_type=decidable_fields.VoteTypeChoices.APPROVAL,
            has_tags_flag=True,
            tags=['for','against','neutral'],
            members_can_add_options=True,
            confirmed=True,
        )
        reason_poll.groups.set(list(self.decidable.get_root_decidable().groups.values_list('id',flat=True)))

        for group in self.decidable.groups.all():
                root_group_decidable_access = self.decidable.get_root_decidable().group_decidable_access.get(group=group)
                group_decidable_access = reason_poll.group_decidable_access.get(group=group)
                group_decidable_access.root_group_decidable_access = root_group_decidable_access
                print('--A--')
                print(root_group_decidable_access.state)
                group_decidable_access.state = root_group_decidable_access.state
                group_decidable_access.save()
    
    def create_linkfile_poll(self):
        title = f'linkfile poll for {self.option.title}'
        if len(title)>120:
            title = title[:117]+'...'
        
        linkfile_poll = decidable_models.Decidable.objects.create(
            title = title,
            root_decidable = self.decidable.get_root_decidable(),
            parent_option = self.option,
            created_by = self.decidable.created_by,
            decidable_type=decidable_fields.DecidableTypeChoices.LINKFILEPOLL,
            voting_type=decidable_fields.VoteTypeChoices.APPROVAL,
            members_can_add_options=True,
            confirmed=True,
            state=self.decidable.get_root_decidable().state
        )
        linkfile_poll.groups.set(list(self.decidable.get_root_decidable().groups.values_list('id',flat=True)))
        
    def create_feed_channel(self):
        decidable_option = self.option.decidable_option.get(
            decidable=self.decidable
        )

        for group_decidable_option_access in decidable_option.group_decidable_option_access.all():
            channel = Channel.objects.create(
                type=ChannelTypechoices.OPTION,
                title=f'{self.decidable.title} Feed'
            )
            group_decidable_option_access.feed_channel = channel
            group_decidable_option_access.save()
        
            # Add Add all users in decidable groups to channel
            group_users = GroupUser.objects.filter(
                group__in=decidable_option.groups.all()
            )
            channel.participants.add(*group_users)
