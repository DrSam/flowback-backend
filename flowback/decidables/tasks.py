from flowback.decidables import models as decidable_models
from flowback.user.models import User
from django.db import transaction
from django.db.models import Sum, Avg
from flowback.decidables.fields import DecidableTypeChoices
from flowback.decidables.fields import VoteTypeChoices
from feed.models import Channel
from feed.fields import ChannelTypechoices
import importlib
import numpy as np
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import datetime
from datetime import timedelta

def setup_channel(decidable):
    # only create channels for certain types of decidables
    if decidable.decidable_type in ['poll','aspect','vote','challenge','election']:
        channel = Channel.objects.create(
            type=ChannelTypechoices.DECIDABLE,
            title=f'{decidable.title} Feed',
            decidable=decidable
        )


def open_decidable(decidable):
    """
    Polls, votes, challenges, elections, that are root decidables are open when confirmed
    """
    if (
        decidable.is_root_decidable 
        and 
        decidable.decidable_type in ['poll','aspect','vote','challenge','election']
    ):
        pass

def after_decidable_confirm(decidable_id):
    decidable = decidable_models.Decidable.objects.get(id=decidable_id)
    module = importlib.import_module(f'flowback.decidables.classes.{decidable.decidable_type}')
    _class = getattr(module,'Decidable')
    instance = _class(decidable=decidable)
    instance.on_confirm()
    

def after_decidable_create(decidable_id):
    decidable = decidable_models.Decidable.objects.get(id=decidable_id)
    module = importlib.import_module(f'flowback.decidables.classes.{decidable.decidable_type}')
    _class = getattr(module,'Decidable')
    instance = _class(decidable=decidable)
    instance.on_create()


def after_option_create(option_id,decidable_id):
    option = decidable_models.Option.objects.get(id=option_id)
    decidable = decidable_models.Decidable.objects.get(id=decidable_id)
    module = importlib.import_module(f'flowback.decidables.classes.{decidable.decidable_type}')
    _class = getattr(module,'Decidable')
    instance = _class(decidable=decidable)
    instance.on_option_create(option)


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
            group__group_users__user=user,
            group__group_users__active=True
        )

        # Set the user's vote for all of the above groups with the current vote
        for group_decidable_option_access in group_decidable_option_accesses:
            group_user = group_decidable_option_access.group.group_users.get(
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
            if group_decidable_option_access.decidable_option.decidable.voting_type in ['approval','score']:
                group_decidable_option_access.value = group_decidable_option_access.group_user_decidable_option_vote.aggregate(Sum('value'))['value__sum'] or 0
            if group_decidable_option_access.decidable_option.decidable.voting_type in ['rating']:
                group_decidable_option_access.value = group_decidable_option_access.group_user_decidable_option_vote.aggregate(Avg('value'))['value__avg'] or 0


            group_users = group_decidable_option_access.group.group_users.count()
            voted_group_users = group_decidable_option_access.voters.count()
            # Count positive votes
            if group_decidable_option_access.decidable_option.decidable.voting_type == 'approval':
                favorable_voted_group_users = group_decidable_option_access.group_user_decidable_option_vote.filter(value=1).count()
            elif group_decidable_option_access.decidable_option.decidable.voting_type == 'score':
                favorable_voted_group_users = group_decidable_option_access.group_user_decidable_option_vote.filter(value__gt=0).count()
            elif group_decidable_option_access.decidable_option.decidable.voting_type == 'rating':
                favorable_voted_group_users = group_decidable_option_access.group_user_decidable_option_vote.filter(value__gte=3).count()
            

            # Calculate quorum
            group_decidable_option_access.quorum = np.round(voted_group_users*100.0/group_users) 
            
            # Calculate approval
            group_decidable_option_access.approval = np.round(favorable_voted_group_users*100.0/voted_group_users) 

            # Check if passed quorum and approval
            if (
                group_decidable_option_access.quorum >= decidable.quorum
                and
                group_decidable_option_access.approval >= decidable.approval_minimum
            ):
                if not group_decidable_option_access.passed_flag:
                    group_decidable_option_access.passed_flag = True
                    group_decidable_option_access.passed_timestamp = timezone.now()
            else:
                if group_decidable_option_access.passed_flag:
                    group_decidable_option_access.passed_flag = False
                    group_decidable_option_access.passed_timestamp = None

            group_decidable_option_access.save()
        

def update_decidable_votes(decidable_id,user_id,vote):
    decidable = decidable_models.Decidable.objects.get(id=decidable_id)
    user = User.objects.get(id=user_id)

    with transaction.atomic():
        group_decidable_accesses = decidable.group_decidable_access.filter(
            group__group_users__user=user,
            group__group_users__active=True
        )

        # Set the user's vote for all of the above groups with the current vote
        for group_decidable_access in group_decidable_accesses:
            group_user = group_decidable_access.group.group_users.get(
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


def compute_voting_results():
    # Annotate number of options that have passed quorum
    decidable_group_access = decidable_models.GroupDecidableAccess.objects.filter(
        decidable__decidable_type='vote',
        decidable__state='open',
    ).filter(
        Q(
            Q(decidable__closes_on_end_date=True)
            &
            Q(
                Q(decidable__end_date__lte=timezone.now().date())
                |
                Q(decidable__root_decidable__end_date__lte=timezone.now().date())
            )
        )
        |
        Q(
            decidable__closes_on_finalization_period=True
        )
    )
    for decidable_group in decidable_group_access:
        # First check if some have passed quorum and approval
        if decidable_group.decidable.closes_on_finalization_period:
            if not decidable_group.decidable.has_winners:
                group_decidable_option_access = decidable_models.GroupDecidableOptionAccess.objects.filter(
                    decidable_option__decidable=decidable_group.decidable,
                    group=decidable_group.group,
                    passed_flag=True,
                ).order_by('-value')
                if group_decidable_option_access.filter(
                    passed_timestamp__gte=timezone.now()-timedelta(days=decidable_group.decidable.finalization_period)
                ).exists():
                    if group_decidable_option_access.count()>0:
                        group_decidable_option_access.update(winner=True)
                        group_decidable_option_access.fsm.end_poll()
                        #TODO: Take snapshot
            else:
                group_decidable_option_access = decidable_models.GroupDecidableOptionAccess.objects.filter(
                    decidable_option__decidable=decidable_group.decidable,
                    group=decidable_group.group,
                    passed_flag=True,
                    passed_timestamp__gte=timezone.now()-timedelta(days=decidable_group.decidable.finalization_period)
                ).order_by('-value')[:decidable_group.decidable.num_winners]
                if group_decidable_option_access.count()==decidable_group.decidable.num_winners:
                    group_decidable_option_access.update(winner=True)
                    group_decidable_option_access.fsm.end_poll()
                    #TODO: Take snapshot
    
        if decidable_group.decidable.closes_on_end_date:
            if not decidable_group.decidable.has_winners:
                group_decidable_option_access = decidable_models.GroupDecidableOptionAccess.objects.filter(
                    decidable_option__decidable=decidable_group.decidable,
                    group=decidable_group.group,
                    passed_flag=True,
                ).order_by('-value')
                if group_decidable_option_access.count()>0:
                    group_decidable_option_access.update(winner=True)
                    group_decidable_option_access.fsm.end_poll()
                    #TODO: Take snapshot
            else:
                group_decidable_option_access = decidable_models.GroupDecidableOptionAccess.objects.filter(
                    decidable_option__decidable=decidable_group.decidable,
                    group=decidable_group.group,
                    passed_flag=True,
                ).order_by('-value')[:decidable_group.decidable.num_winners]
                if group_decidable_option_access.count()>0:
                    group_decidable_option_access.update(winner=True)
                    group_decidable_option_access.fsm.end_poll()
                    #TODO: Take snapshot
                

            


