from django.db.models import Sum, Q, Count, F, OuterRef, Subquery
from rest_framework.exceptions import ValidationError

from backend.settings import SCORE_VOTE_CEILING, SCORE_VOTE_FLOOR
from flowback.common.services import get_object
from flowback.group.models import GroupUserDelegatePool, GroupUser
from flowback.poll.models import Poll, PollProposal, PollVoting, PollVotingTypeRanking, PollDelegateVoting, \
    PollVotingTypeForAgainst, PollVotingTypeCardinal
from flowback.group.selectors import group_user_permissions
from flowback.group.services import group_schedule
from django.utils import timezone


def poll_proposal_vote_update(*, user_id: int, poll_id: int, data: dict) -> None:
    poll = get_object(Poll, id=poll_id)
    group_user = group_user_permissions(user=user_id,
                                        group=poll.created_by.group.id,
                                        permissions=['allow_vote', 'admin'])

    if poll.current_phase != 'vote':
        raise ValidationError("Unable to cast votes outside of vote phase")

    if poll.poll_type == Poll.PollType.RANKING:
        if not data['votes']:
            PollVoting.objects.filter(created_by=group_user, poll=poll).delete()
            return

        proposals = poll.pollproposal_set.filter(id__in=[x for x in data['votes']]).all()
        if len(proposals) != len(data['votes']):
            raise ValidationError('Not all proposals are available to vote for')

        poll_vote, created = PollVoting.objects.get_or_create(created_by=group_user, poll=poll)
        poll_vote_ranking = [PollVotingTypeRanking(author=poll_vote,
                                                   proposal_id=proposal,
                                                   priority=len(data['votes']) - priority)
                             for priority, proposal in enumerate(data['votes'])]
        PollVotingTypeRanking.objects.filter(author=poll_vote).delete()
        PollVotingTypeRanking.objects.bulk_create(poll_vote_ranking)

    elif poll.poll_type == Poll.PollType.CARDINAL:

        if SCORE_VOTE_CEILING is not None and any([score >= SCORE_VOTE_CEILING for score in data['score']]):
            raise ValidationError(f'Voting scores exceeds ceiling bounds (currently set at {SCORE_VOTE_CEILING})')

        if SCORE_VOTE_FLOOR is not None and any([score <= SCORE_VOTE_FLOOR for score in data['score']]):
            raise ValidationError(f'Voting scores exceeds floor bounds (currently set at {SCORE_VOTE_FLOOR})')

        # Delete votes if no polls are registered
        if not data['proposals']:
            PollVoting.objects.filter(created_by=group_user, poll=poll).delete()
            return

        if len(data['scores'] != len(data['proposals'])):
            raise ValidationError("The amount of votes don't match the amount of polls")

        proposals = poll.pollproposal_set.filter(id__in=data['proposals']).all()
        if len(proposals) != len(data['proposals']):
            raise ValidationError('Not all proposals are available to vote for')

        user_vote, created = PollVoting.objects.get_or_create(created_by=group_user, poll=poll)
        poll_vote_cardinal = [PollVotingTypeCardinal(author=user_vote,
                                                     proposal_id=data['proposals'][i],
                                                     score=data['scores'][i])
                             for i in range(len(data['proposals']))]

        PollVotingTypeCardinal.objects.filter(author=user_vote).delete()
        PollVotingTypeCardinal.objects.bulk_create(poll_vote_cardinal)

    elif poll.poll_type == Poll.PollType.SCHEDULE:
        if not data['votes']:
            PollVoting.objects.filter(created_by=group_user, poll=poll).delete()
            return

        proposals = poll.pollproposal_set.filter(id__in=data['votes']).all()

        if len(proposals) != len(data['votes']):
            raise ValidationError('Not all proposals are available to vote for')

        poll_vote, created = PollVoting.objects.get_or_create(created_by=group_user, poll=poll)
        poll_vote_schedule = [PollVotingTypeForAgainst(author=poll_vote,
                                                       proposal_id=proposal,
                                                       vote=True)
                              for proposal in data['votes']]
        PollVotingTypeForAgainst.objects.filter(author=poll_vote).delete()
        PollVotingTypeForAgainst.objects.bulk_create(poll_vote_schedule)

    else:
        raise ValidationError('Unknown poll type')


# TODO update in future for delegate pool
def poll_proposal_delegate_vote_update(*, user_id: int, poll_id: int, data) -> None:
    poll = get_object(Poll, id=poll_id)
    group_user = group_user_permissions(user=user_id, group=poll.created_by.group.id)
    delegate_pool = get_object(GroupUserDelegatePool, groupuserdelegate__group_user=group_user)

    if group_user.group.id != poll.created_by.group.id:
        raise ValidationError('Permission denied')

    if poll.current_phase != 'delegate_vote':
        raise ValidationError("Unable to cast votes outside of delegate vote phase")

    if poll.poll_type == Poll.PollType.RANKING:
        if not data['votes']:
            PollDelegateVoting.objects.filter(created_by=delegate_pool, poll=poll).delete()
            return

        proposals = poll.pollproposal_set.filter(id__in=data['votes']).all()

        if len(proposals) != len(data['votes']):
            raise ValidationError('Not all proposals are available to vote for')

        poll_vote, created = PollDelegateVoting.objects.get_or_create(created_by=delegate_pool, poll=poll)
        poll_vote_ranking = [PollVotingTypeRanking(author_delegate=poll_vote,
                                                   proposal_id=proposal,
                                                   priority=len(data['votes']) - priority)
                             for priority, proposal in enumerate(data['votes'])]
        PollVotingTypeRanking.objects.filter(author_delegate=poll_vote).delete()
        PollVotingTypeRanking.objects.bulk_create(poll_vote_ranking)

    elif poll.poll_type == Poll.PollType.CARDINAL:

        # Delete votes if no polls are registered
        if not data['proposals']:
            PollDelegateVoting.objects.filter(created_by=delegate_pool, poll=poll).delete()
            return

        if len(data['scores'] != len(data['proposals'])):
            raise ValidationError("The amount of votes don't match the amount of polls")

        proposals = poll.pollproposal_set.filter(id__in=data['proposals']).all()
        if len(proposals) != len(data['proposals']):
            raise ValidationError('Not all proposals are available to vote for')

        pool_vote, created = PollDelegateVoting.objects.get_or_create(created_by=delegate_pool, poll=poll)
        poll_vote_cardinal = [PollVotingTypeCardinal(author_delegate=pool_vote,
                                                     proposal_id=data['proposals'][i],
                                                     score=data['scores'][i])
                             for i in range(len(data['proposals']))]

        PollVotingTypeCardinal.objects.filter(author_delegate=pool_vote).delete()
        PollVotingTypeCardinal.objects.bulk_create(poll_vote_cardinal)

    elif poll.poll_type == Poll.PollType.SCHEDULE:
        if not data['votes']:
            PollDelegateVoting.objects.filter(created_by=delegate_pool, poll=poll).delete()
            return

        proposals = poll.pollproposal_set.filter(id__in=data['votes']).all()

        if len(proposals) != len(data['votes']):
            raise ValidationError('Not all proposals are available to vote for')

        poll_vote, created = PollDelegateVoting.objects.get_or_create(created_by=delegate_pool, poll=poll)
        poll_vote_schedule = [PollVotingTypeForAgainst(author_delegate=poll_vote,
                                                       proposal_id=proposal,
                                                       vote=True)
                              for proposal in enumerate(data['votes'])]
        PollVotingTypeForAgainst.objects.filter(author_delegate=poll_vote).delete()
        PollVotingTypeForAgainst.objects.bulk_create(poll_vote_schedule)

    else:
        raise ValidationError('Unknown poll type')


def poll_proposal_vote_count(*, poll_id: int) -> None:
    poll = get_object(Poll, id=poll_id)
    group = poll.created_by.group
    total_proposals = poll.pollproposal_set.count()

    # Count mandate for each delegate, multiply it by score
    mandate = GroupUserDelegatePool.objects.filter(polldelegatevoting__poll=poll).aggregate(
        mandate=Count('groupuserdelegator',
                      filter=~Q(groupuserdelegator__delegator__pollvoting__poll=poll) &
                      Q(groupuserdelegator__tags__in=[poll.tag])))['mandate']

    mandate_subquery = GroupUserDelegatePool.objects.filter(id=OuterRef('author_delegate__created_by')).annotate(
        mandate=Count('groupuserdelegator',
                      filter=~Q(groupuserdelegator__delegator__pollvoting__poll=poll) &
                             Q(groupuserdelegator__tags__in=[poll.tag]))).values('mandate')

    if poll.poll_type == Poll.PollType.RANKING:
        if poll.tag:
            delegate_votes = PollVotingTypeRanking.objects.filter(author_delegate__poll=poll).values('pk').annotate(
                score=(total_proposals - (Count('author_delegate__pollvotingtyperanking') - F('priority'))) *
                Subquery(mandate_subquery))

            # Set score to the same as priority for user votes
            user_votes = PollVotingTypeRanking.objects.filter(author__poll=poll
                                                              ).values('pk').annotate(
                score=total_proposals - (Count('author__pollvotingtyperanking') - F('priority')))

            for i in user_votes:
                PollVotingTypeRanking.objects.filter(id=i['pk']).update(score=i['score'])

            for i in delegate_votes:
                PollVotingTypeRanking.objects.filter(id=i['pk']).update(score=i['score'])

            # TODO make this work, replace both above
            # PollVotingTypeRanking.objects.bulk_update(delegate_votes | user_votes, fields=('score',))

            # Update scores on each proposal, Summarize both regular votes and delegate votes
            proposals = PollProposal.objects.filter(poll_id=poll_id).values('pk') \
                .annotate(score=Sum('pollvotingtyperanking__score'))

            for i in proposals:
                PollProposal.objects.filter(id=i['pk']).update(score=i['score'])

            # TODO make this work aswell, replace above
            # PollProposal.objects.bulk_update(proposals, fields=('score',))

            poll.participants = mandate + PollVoting.objects.filter(poll=poll).all().count()
            poll.save()

    if poll.poll_type == Poll.PollType.CARDINAL:
        if poll.tag:
            user_proposal_scores = PollVotingTypeCardinal.objects.filter(author__poll=OuterRef('poll')).values('score')
            delegate_proposal_scores = PollVotingTypeCardinal.objects.filter(author_delegate__poll=OuterRef('poll')
                                            ).annotate(final_score=F('score') * Subquery(mandate_subquery)).values('final_score')

            PollProposal.objects.filter(poll=poll).update(score=Subquery(user_proposal_scores) + Subquery(delegate_proposal_scores))

    if poll.poll_type == Poll.PollType.SCHEDULE:
        if poll.tag:
            delegate_votes = PollVotingTypeForAgainst.objects.filter(author_delegate__poll=poll).values('pk').annotate(
                score=(Count('author_delegate__pollvotingtypeforagainst',
                             filter=Q(vote=True)) * Subquery(mandate_subquery) -
                       Count('author_delegate__pollvotingtypeforagainst',
                             filter=Q(vote=False)) * Subquery(mandate_subquery)))

            # Set score to the same as priority for user votes
            user_votes = PollVotingTypeForAgainst.objects.filter(author__poll=poll, vote=True).values('pk', 'vote')

            for i in user_votes:
                PollVotingTypeForAgainst.objects.filter(id=i['pk']).update(score=int(i['vote']))

            for i in delegate_votes:
                PollVotingTypeForAgainst.objects.filter(id=i['pk']).update(score=int(i['vote']))

            # TODO make this work, replace both above (Copied from ranking comment)
            # PollVotingTypeSchedule.objects.bulk_update(delegate_votes | user_votes, fields=('score',))

            # Update scores on each proposal, Summarize both regular votes and delegate votes
            proposals = PollProposal.objects.filter(poll_id=poll_id).values('pk') \
                .annotate(score=Sum('pollvotingtypeforagainst__score'))

            for i in proposals:
                PollProposal.objects.filter(id=i['pk']).update(score=i['score'])

            # TODO make this work aswell, replace above
            # PollProposal.objects.bulk_update(proposals, fields=('score',))

            poll.participants = mandate + PollVoting.objects.filter(poll=poll).all().count()
            total_group_users = GroupUser.objects.filter(group=group).count()

            # Check if poll reaches quorum limits
            if total_group_users / poll.participants < \
               (poll.quorum if poll.quorum is not None else group.default_quorum) / 100:
                poll.status = -1

            else:
                poll.status = 1

            poll.save()
