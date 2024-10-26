from flowback.decidables import models as decidable_models
from flowback.user.models import User
from django.db import transaction
from django.db.models import Sum
from flowback.decidables.fields import DecidableTypeChoices
from flowback.decidables.fields import VoteTypeChoices

def after_decidable_confirm(decidable_id):
    decidable = decidable_models.Decidable.objects.get(id=decidable_id)
    with transaction.atomic():
        for option in decidable.options.all():
            # Create a reason poll
            reason_poll = decidable_models.Decidable.objects.create(
                root_decidable = option.root_decidable,
                reason_option = option,
                created_by = decidable.created_by,
                decidable_type=DecidableTypeChoices.REASONPOLL,
                voting_type=VoteTypeChoices.APPROVAL,
                has_tags_flag=True,
                tags=['for','against','neutral'],
                members_can_add_options=True,
                confirmed=True,
            )
            reason_poll.groups.set(list(decidable.groups.values_list('id',flat=True)))





def update_option_votes(decidable_id,option_id,user_id,vote):
    decidable = decidable_models.Decidable.objects.get(id=decidable_id)
    option = decidable_models.Option.objects.get(id=option_id)
    decidable_option = option.decidable_option.filter(
        decidable = decidable
    ).first()
    
    user = User.objects.get(id=user_id)

    with transaction.atomic():
        # Get groups with access to option, that the user is a part of
        group_decidable_option_accesses = decidable_option.group_decidable_option_access.filter(
            group__groupuser__user=user,
            group__groupuser__active=True
        )

        # Set the user's vote for all of the above groups with the current vote
        for group_decidable_option_access in group_decidable_option_accesses:
            group_user = group_decidable_option_access.group.groupuser_set.get(
                user=user,
                active=True
            )
            decidable_models.GroupUserDecidableOptionVote.objects.update_or_create(
                group_decidable_option_access=group_decidable_option_access,
                group_user=group_user,
                defaults={
                    'value':vote
                }
            )

        # For each group, update votes
        for group_decidable_option_access in group_decidable_option_accesses:
            group_decidable_option_access.value = group_decidable_option_access.group_user_decidable_option_vote.aggregate(Sum('value'))['value__sum'] or 0
            group_decidable_option_access.save()
        

def update_decidable_votes(decidable_id,user_id,vote):
    decidable = decidable_models.Decidable.objects.get(id=decidable_id)
    user = User.objects.get(id=user_id)

    with transaction.atomic():
        group_decidable_accesses = decidable.group_decidable_access.filter(
            group__groupuser__user=user,
            group__groupuser__active=True
        )

        # Set the user's vote for all of the above groups with the current vote
        for group_decidable_access in group_decidable_accesses:
            group_user = group_decidable_access.group.groupuser_set.get(
                user=user,
                active=True
            )
            decidable_models.GroupUserDecidableVote.objects.update_or_create(
                group_decidable_access=group_decidable_access,
                group_user=group_user,
                defaults={
                    'value':vote
                }
            )

        # For each group, update votes
        for group_decidable_access in group_decidable_accesses:
            group_decidable_access.value = group_decidable_access.group_user_decidable_vote.aggregate(Sum('value'))['value__sum'] or 0
            group_decidable_access.save()