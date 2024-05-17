from django.utils import timezone
from rest_framework.exceptions import ValidationError

from flowback.common.services import get_object
from flowback.files.services import upload_collection
from flowback.group.selectors import group_user_permissions
from flowback.poll.models import PollProposal, Poll, PollProposalTypeSchedule, PollProposalPriority
from flowback.group.models import Group

# TODO proposal can be created without schedule, dangerous
from flowback.poll.services.poll import poll_refresh_cheap
from flowback.schedule.models import ScheduleEvent


def poll_proposal_create(*, user_id: int, poll_id: int,
                         title: str = None, description: str = None, attachments=None, **data) -> PollProposal:
    poll = get_object(Poll, id=poll_id)
    group_user = group_user_permissions(user=user_id, group=poll.created_by.group.id,
                                        permissions=['create_proposal', 'admin'])

    if group_user.group.id != poll.created_by.group.id:
        raise ValidationError('Permission denied')

    poll.check_phase('proposal', 'dynamic', 'schedule')

    if poll.poll_type == Poll.PollType.SCHEDULE and group_user.user.id != poll.created_by.user.id:
        raise ValidationError('Only poll author can create proposals for schedule polls')

    proposal = PollProposal(created_by=group_user, poll=poll, title=title, description=description)
    proposal.full_clean()

    collection = None
    if attachments:
        collection = upload_collection(user_id=user_id, file=attachments, upload_to="group/poll/proposals")

    proposal.attachments = collection
    proposal.save()

    if poll.poll_type == Poll.PollType.SCHEDULE:
        if not (data.get('start_date') and data.get('end_date')):
            raise Exception('Missing start_date and/or end_date, for proposal schedule creation')

        event = ScheduleEvent(schedule=poll.polltypeschedule.schedule,
                              title=f"group_poll_{poll_id}_event",
                              start_date=data['start_date'],
                              end_date=data['end_date'],
                              origin_name=PollProposal.schedule_origin,
                              origin_id=proposal.id)

        event.full_clean()
        event.save()

        schedule_proposal = PollProposalTypeSchedule(proposal=proposal,
                                                     event=event)

        try:
            schedule_proposal.full_clean()

        except ValidationError as e:
            proposal.delete()
            raise e

        schedule_proposal.save()

    return proposal


def poll_proposal_delete(*, user_id: int, proposal_id: int) -> None:
    proposal = get_object(PollProposal, id=proposal_id)
    group_user = group_user_permissions(group=proposal.created_by.group, user=user_id)
    poll_refresh_cheap(poll_id=proposal.poll.id)  # TODO get celery

    if proposal.created_by == group_user and group_user.check_permission(delete_proposal=True):
        proposal.poll.check_phase('proposal', 'dynamic')

    elif not (group_user.check_permission(force_delete_permission=True) or group_user.is_admin):
        raise ValidationError("Deleting other users proposals needs either "
                              "group admin or force_delete_proposal permission")

    proposal.delete()


def poll_proposal_priority_update(user_id: int, proposal_id: int, score: int) -> None:
    proposal = PollProposal.objects.get(id=proposal_id)
    group_user = group_user_permissions(user=user_id, group=proposal.poll.created_by.group)

    if score != 0:
        PollProposalPriority.objects.update_or_create(group_user=group_user,
                                                      proposal=proposal,
                                                      defaults=dict(score=score))

    else:
        PollProposalPriority.objects.get(group_user=group_user, proposal=proposal).delete()

    check_poll_proposal_met_approval_and_quorum(proposal_id=proposal_id)


def check_poll_proposal_met_approval_and_quorum(*,proposal_id:int) -> bool:
    """
    Determines whether a poll proposal has achieved the necessary approval and quorum to become inactive.
    """

    try:
        proposal = PollProposal.objects.get(id=proposal_id)
        poll = Poll.objects.get(id=proposal.poll_id)
    except (PollProposal.DoesNotExist, Poll.DoesNotExist):
        print('Poll proposal or poll does not exist')
        return False
    
    poll_community = poll.created_by.group
    total_community_members = Group.objects.get(id=poll_community.id).groupuser_set.count()

    # positive_proposal_votes = proposal.positive_votes
    positive_proposal_votes = PollProposalPriority.objects.filter(proposal=proposal, score__gt=0).count()
    print("positive_proposal_votes", positive_proposal_votes)

    if poll.quorum is None:
        print('No quorum set for poll')
        return False
    
    if poll.approval_minimum is None:
        print('No approval minimum set for poll')
        return False

    # percentage of community members that have voted
    total_proposal_votes = PollProposalPriority.objects.filter(proposal=proposal).count()
    total_voted_community_members_percentage = (total_proposal_votes / total_community_members) * 100

    if positive_proposal_votes == 0:
        print('No positive votes for poll proposal')
        return False
    
    # percentage of positive votes
    positive_votes_percentage = (positive_proposal_votes / total_proposal_votes) * 100

    if total_voted_community_members_percentage >= poll.quorum and positive_votes_percentage >= poll.approval_minimum:
        print('Poll proposal has met approval and quorum')
        poll.status = 1
        poll.save()
        return True
    
    return False