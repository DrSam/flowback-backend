from flowback.group.models import GroupUser
from feed.models import Channel
from feed.fields import ChannelTypechoices
from django.db.models import Q


def add_user_to_group(group,user,admin=False):
    # Create group user
    group_user,_ = GroupUser.objects.update_or_create(
        group=group,
        user=user,
        defaults={
            'active':True,
            'is_admin':admin
        }
    )

    # Find channels to add user to
    channels = Channel.objects.filter(
        Q(
            Q(type=ChannelTypechoices.GROUP)
            &
            Q(group=group)
        )
        |
        Q(
            Q(
                type=ChannelTypechoices.DECIDABLE
            )
            &
            Q(
                group_decidables__group=group
            )
        )
        |
        Q(
            Q(
                type=ChannelTypechoices.OPTION
            )
            &
            Q(
                group_decidable_option__group=group
            )
        )
    )

    for channel in channels:
        channel.participants.add(group_user)


    