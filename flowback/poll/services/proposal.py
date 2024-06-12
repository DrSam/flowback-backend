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


def poll_proposal_create(*, user_id: int,
                         poll_id: int,
                         title: str = None,
                         description: str = None,
                         attachments=None,
                         blockchain_id: int = None,
                         **data) -> PollProposal:
    poll = get_object(Poll, id=poll_id)
    group_user = group_user_permissions(user=user_id, group=poll.created_by.group.id,
                                        permissions=['create_proposal', 'admin'])

    if group_user.group.id != poll.created_by.group.id:
        raise ValidationError('Permission denied')

    poll.check_phase('proposal', 'dynamic', 'schedule')

    if poll.poll_type == Poll.PollType.SCHEDULE and group_user.user.id != poll.created_by.user.id:
        raise ValidationError('Only poll author can create proposals for schedule polls')

    proposal = PollProposal(created_by=group_user,
                            poll=poll,
                            title=title,
                            description=description,
                            blockchain_id=blockchain_id)
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

    check_poll_met_approval_and_quorum(proposal_id=proposal_id)


def check_poll_met_approval_and_quorum(*,proposal_id:int) -> bool:
    """
    Check if a proposal within a poll has met the necessary approval and quorum requirements
    to move to the finalization period.

    Args:
        proposal_id (int): The ID of the proposal to check.

    Returns:
        bool: True if the proposal has met both approval and quorum requirements, False otherwise.
    
    The function performs the following steps:
        1. Retrieves the proposal and associated poll from the database.
        2. Calculates the total number of active members in the poll's community.
        3. Counts the number of positive votes for the proposal.
        4. Checks if the poll's quorum and approval minimum values are set.
        5. Calculates the percentage of community members that have voted.
        6. Calculates the percentage of positive votes out of total votes.
        7. Updates the poll status to 'finalization period' if both approval and quorum criteria are met,
           otherwise sets it to 'ongoing'.
    """

    try:
        proposal = PollProposal.objects.get(id=proposal_id)
        poll = Poll.objects.get(id=proposal.poll_id)
    except (PollProposal.DoesNotExist, Poll.DoesNotExist):
        return False
    
    poll_community = poll.created_by.group
    total_community_members = Group.objects.get(id=poll_community.id).groupuser_set.filter(user__is_active=True).count()
    positive_proposal_votes = PollProposalPriority.objects.filter(proposal=proposal, score__gt=0).count()

    # percentage of community members that have voted
    total_proposal_votes = PollProposalPriority.objects.filter(proposal=proposal).count()
    total_voted_community_members_percentage = (total_proposal_votes / total_community_members) * 100

    if positive_proposal_votes == 0:
        return False
    
    # percentage of positive votes
    positive_votes_percentage = (positive_proposal_votes / total_proposal_votes) * 100

    if total_voted_community_members_percentage >= poll.quorum and positive_votes_percentage >= poll.approval_minimum:
        poll.status = 2 #finalization period
        poll.finalization_period_start_date = timezone.now() 
        poll.save()
        return True
    else:
        poll.status = 0 #ongoing
        poll.finalization_period_start_date = None
        poll.save()
        return False
    