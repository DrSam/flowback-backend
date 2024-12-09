import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from django.db.models.signals import post_save, post_delete, pre_save
from django.forms import model_to_dict
from rest_framework.exceptions import ValidationError

from backend.settings import FLOWBACK_DEFAULT_GROUP_JOIN
from flowback.chat.models import MessageChannel, MessageChannelParticipant
from flowback.chat.services import message_channel_create, message_channel_join
from flowback.comment.models import CommentSection
from flowback.comment.services import comment_section_create, comment_section_create_model_default
from flowback.common.models import BaseModel
from flowback.common.services import get_object
from flowback.files.models import FileCollection
from flowback.kanban.models import Kanban
from flowback.kanban.services import kanban_create, kanban_subscription_create, kanban_subscription_delete
from flowback.schedule.models import Schedule
from flowback.schedule.services import create_schedule
from flowback.user.models import User
from django.db import models
from flowback.group.fields import GroupUserInviteStatusChoices

# Create your models here.
class GroupFolder(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f'{self.id} - {self.name}'


class Group(BaseModel):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    is_hub_group = models.BooleanField(default=False)

    # Direct join determines if join requests requires moderation or not.
    direct_join = models.BooleanField(default=False)

    # Public determines if the group is open to public or not
    public = models.BooleanField(default=True)

    # Determines the default permission for every user get when they join
    # TODO return basic permissions by default if field is NULL
    default_permission = models.OneToOneField('GroupPermissions',
                                              null=True,
                                              blank=True,
                                              on_delete=models.SET_NULL)

    name = models.TextField(unique=True)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='group/image', null=True, blank=True)
    cover_image = models.ImageField(upload_to='group/cover_image', null=True, blank=True)
    hide_poll_users = models.BooleanField(default=False)  # Hides users in polls, TODO remove bool from views
    default_quorum = models.IntegerField(default=50, validators=[MinValueValidator(1), MaxValueValidator(100)])
    default_approval_minimum = models.PositiveIntegerField(default=51, validators=[MinValueValidator(1), MaxValueValidator(100)])
    default_finalization_period = models.PositiveIntegerField(default=3,validators=[MinValueValidator(1), MaxValueValidator(30)],)
    schedule = models.ForeignKey(Schedule, null=True, blank=True, on_delete=models.PROTECT)
    kanban = models.ForeignKey(Kanban, null=True, blank=True, on_delete=models.PROTECT)
    chat = models.ForeignKey(MessageChannel, on_delete=models.PROTECT,null=True,blank=True)
    group_folder = models.ForeignKey(GroupFolder, null=True, blank=True, on_delete=models.SET_NULL)
    blockchain_id = models.PositiveIntegerField(null=True, blank=True)

    jitsi_room = models.UUIDField(unique=True, default=uuid.uuid4)

    class Meta:
        constraints = [models.CheckConstraint(check=~Q(Q(public=False) & Q(direct_join=True)),
                                              name='group_not_public_and_direct_join_check')]
    
    def __str__(self):
        return self.name


class Topic(BaseModel):
    group = models.ForeignKey(
        Group,
        related_name='topics',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True, default='')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['group', 'name'], name='group_unique_topics')]


# Permission class for each Group
class GroupPermissions(BaseModel):
    role_name = models.TextField()
    author = models.ForeignKey('Group', on_delete=models.CASCADE)
    invite_user = models.BooleanField(default=True)
    create_poll = models.BooleanField(default=True)
    poll_fast_forward = models.BooleanField(default=False)
    poll_quorum = models.BooleanField(default=False)
    allow_vote = models.BooleanField(default=True)
    kick_members = models.BooleanField(default=False)
    ban_members = models.BooleanField(default=False)

    create_proposal = models.BooleanField(default=True)
    update_proposal = models.BooleanField(default=True)
    delete_proposal = models.BooleanField(default=True)

    prediction_statement_create = models.BooleanField(default=True)
    prediction_statement_update = models.BooleanField(default=True)
    prediction_statement_delete = models.BooleanField(default=True)

    prediction_bet_create = models.BooleanField(default=True)
    prediction_bet_update = models.BooleanField(default=True)
    prediction_bet_delete = models.BooleanField(default=True)

    create_kanban_task = models.BooleanField(default=True)
    update_kanban_task = models.BooleanField(default=True)
    delete_kanban_task = models.BooleanField(default=True)

    force_delete_poll = models.BooleanField(default=False)
    force_delete_proposal = models.BooleanField(default=False)
    force_delete_comment = models.BooleanField(default=False)

    @staticmethod
    def negate_field_perms():
        return ['id', 'created_at', 'updated_at', 'role_name', 'author']


# Permission Tags for each group, and for user to put on delegators
class GroupTags(BaseModel):
    name = models.TextField()
    group = models.ForeignKey('Group', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    # interval_mean_absolute_error = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    class Meta:
        unique_together = ('name', 'group')


# User information for the specific group
class GroupUser(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='group_users')
    group = models.ForeignKey(Group, on_delete=models.CASCADE,related_name='group_users')
    is_admin = models.BooleanField(default=False)
    permission = models.ForeignKey(GroupPermissions, null=True, blank=True, on_delete=models.SET_NULL)
    chat_participant = models.ForeignKey(MessageChannelParticipant, on_delete=models.PROTECT,null=True,blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'({self.group} - {self.user})'


    # Check if every permission in a dict is matched correctly
    def check_permission(self, raise_exception: bool = False, **permissions):
        if self.permission:
            user_permissions = model_to_dict(self.permission)
        else:
            if self.group.default_permission:
                user_permissions = model_to_dict(self.group.default_permission)
            else:
                fields = [field for field in GroupPermissions._meta.get_fields() if not (field.auto_created
                          or field.name in GroupPermissions.negate_field_perms())]
                user_permissions = {field.name: field.default for field in fields}

        def validate_perms():
            for perm, val in permissions.items():
                if user_permissions.get(perm) != val:
                    yield f"{perm} must be {val}"

        failed_permissions = list(validate_perms())
        if failed_permissions:
            if not raise_exception:
                return False

            raise ValidationError("Unmatched permissions: ", ", ".join(failed_permissions))

        return True

    class Meta:
        unique_together = ('user', 'group')


# GroupThreads are mainly used for creating comment sections for various topics
class GroupThread(BaseModel):
    created_by = models.ForeignKey(GroupUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    pinned = models.BooleanField(default=False)
    comment_section = models.ForeignKey(CommentSection, on_delete=models.DO_NOTHING)
    active = models.BooleanField(default=True)
    attachments = models.ForeignKey(FileCollection, on_delete=models.CASCADE, null=True, blank=True)


class GroupUserInvite(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    email = models.CharField(max_length=128,blank=True,default='')
    external = models.BooleanField()
    status = models.CharField(
        choices=GroupUserInviteStatusChoices.choices,
        default=GroupUserInviteStatusChoices.PENDING
    )
    initiator = models.ForeignKey(
        User,
        related_name='sent_invites', 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )


# A pool containing multiple delegates
# TODO in future, determine if we need the multiple delegates support or not, as we're currently not using it
class GroupUserDelegatePool(BaseModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    blockchain_id = models.PositiveIntegerField(null=True, blank=True, default=None)
    comment_section = models.ForeignKey(CommentSection,
                                        on_delete=models.CASCADE)


# Delegate accounts for group
class GroupUserDelegate(BaseModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)  # TODO no need for two-way group references
    group_user = models.ForeignKey(GroupUser, on_delete=models.CASCADE)
    pool = models.ForeignKey(GroupUserDelegatePool, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('group_user', 'group')


# Delegator to delegate relations
class GroupUserDelegator(BaseModel):
    delegator = models.ForeignKey(GroupUser, on_delete=models.CASCADE, related_name='group_user_delegate_delegator')
    delegate_pool = models.ForeignKey(GroupUserDelegatePool, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    tags = models.ManyToManyField(GroupTags)

    class Meta:
        unique_together = ('delegator', 'delegate_pool', 'group')
