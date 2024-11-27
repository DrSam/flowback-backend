from django.db import models
from django_extensions.db.models import TimeStampedModel
from .fields import DecidableTypeChoices
from .fields import VoteTypeChoices
from .fields import AttachmentChoices
from django.core.validators import MinValueValidator, MaxValueValidator
from flowback.decidables.validators import allowed_image_extensions
from flowback.decidables.fields import DecidableStateChoices


class TitleDescriptionModel(models.Model):
    title = models.CharField(max_length=128, blank=True,default='')
    description = models.CharField(max_length=1024,blank=True,default='')

    class Meta:
        abstract=True


class GroupDecidableAccess(TimeStampedModel):
    group = models.ForeignKey(
        'group.Group',
        related_name='group_decidable_access',
        on_delete=models.CASCADE
    )
    decidable = models.ForeignKey(
        'decidables.Decidable',
        related_name='group_decidable_access',
        on_delete=models.CASCADE
    )

    value = models.IntegerField(default=0)

    voters = models.ManyToManyField(
        'group.GroupUser',
        through='decidables.GroupUserDecidableVote'
    )

    def __str__(self):
        return f'{self.decidable} - {self.group}'


#  Decidable
class Decidable(TimeStampedModel,TitleDescriptionModel):
    state = models.CharField(max_length=32, blank=True,choices=DecidableStateChoices.choices,default=DecidableStateChoices.NOT_STARTED)

    # For aspect decidables
    primary_decidable = models.ForeignKey(
        'self',
        related_name='secondary_decidables',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    topic = models.ForeignKey(
        'group.Topic',
        related_name='decidables',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Parents, for nested decidables
    parent_decidable = models.ForeignKey(
        'self',
        related_name='child_decidables',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    parent_option = models.ForeignKey(
        'decidables.Option',
        related_name='child_decidables',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    is_container = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        'group.GroupUser',
        related_name='decidable',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    groups = models.ManyToManyField(
        'group.Group',
        related_name='decidables',
        through='decidables.GroupDecidableAccess'
    )

    root_decidable = models.ForeignKey(
        'self',
        related_name='descendent_decidables',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    @property
    def is_root_decidable(self):
        return not bool(self.root_decidable)
    
    # Depending on deciable type, code logic will be required to setup decidable properly
    decidable_type = models.CharField(max_length=256,choices=DecidableTypeChoices.choices)
    voting_type = models.CharField(max_length=64, choices=VoteTypeChoices.choices,default=VoteTypeChoices.RATING)

    # Tags may be required when entering an option
    tags = models.JSONField(blank=True,default=list)
    has_tags_flag = models.BooleanField(blank=True,default=False)
    allow_multiple_tags_flag = models.BooleanField(blank=True,default=False)
    members_can_add_options = models.BooleanField(default=False)

    quorum = models.IntegerField(default=51, validators=[MinValueValidator(1), MaxValueValidator(100)])
    approval_minimum = models.PositiveIntegerField(default=51, validators=[MinValueValidator(1), MaxValueValidator(100)])
    finalization_period = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text='Finalization period in days'
    )
    has_winners = models.BooleanField(default=False,blank=True)
    num_winners = models.IntegerField(null=True,blank=True)

    # Decidable options
    active = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    end_date = models.DateField(null=True,blank=True)
    confirmed = models.BooleanField(default=False)

    def get_root_decidable(self):
        return self.root_decidable or self

    def __str__(self):
        return self.title


class GroupDecidableOptionAccess(TimeStampedModel):
    group = models.ForeignKey(
        'group.Group',
        related_name='group_decidable_option_access',
        on_delete=models.CASCADE
    )
    decidable_option = models.ForeignKey(
        'decidables.DecidableOption',
        related_name='group_decidable_option_access',
        on_delete=models.CASCADE
    )

    value = models.IntegerField(default=0)

    voters = models.ManyToManyField(
        'group.GroupUser',
        through='decidables.GroupUserDecidableOptionVote'
    )

    quorum = models.IntegerField(default=0,blank=True)
    approval = models.IntegerField(default=0,blank=True)

    def __str__(self):
        return f'{self.decidable_option} - {self.group}'


class DecidableOption(TimeStampedModel):
    decidable = models.ForeignKey(
        'decidables.Decidable',
        related_name= 'child_options',
        on_delete=models.CASCADE
    )
    option = models.ForeignKey(
        'decidables.Option',
        related_name='decidable_option',
        on_delete=models.CASCADE
    )
    
    groups = models.ManyToManyField(
        'group.Group',
        related_name='decidable_options',
        through='decidables.GroupDecidableOptionAccess'
    )
    # What tags will the option have, assuming parent decidable requires them
    tags = models.JSONField(blank=True,default=list)

    def __str__(self):
        return f'{self.option} - {self.decidable}'


class Option(TimeStampedModel,TitleDescriptionModel):
    decidables = models.ManyToManyField(
        Decidable,
        related_name='options',
        blank=True,
        through='decidables.DecidableOption'
    )
    root_decidable = models.ForeignKey(
        'decidables.Decidable',
        related_name='descendent_options',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    

    def __str__(self):
        return self.title


class Attachment(models.Model):
    type = models.CharField(
        choices=AttachmentChoices.choices,
        max_length=16
    )
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
        blank=True
    )
    decidable = models.ForeignKey(
        Decidable,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        'group.GroupUser',
        related_name='attachments',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    link = models.CharField(max_length=512,blank=True,default='')
    file = models.FileField(null=True,blank=True)
    image = models.ImageField(null=True,blank=True, validators=[allowed_image_extensions])


# Voting classes for decidables
class GroupUserDecidableVote(TimeStampedModel):
    group_decidable_access = models.ForeignKey(
        'decidables.GroupDecidableAccess',
        related_name='group_user_decidable_vote',
        on_delete=models.CASCADE
    )
    group_user = models.ForeignKey(
        'group.GroupUser',
        related_name='group_user_decidable_vote',
        on_delete=models.CASCADE
    )
    value = models.IntegerField(default=0)

 

class GroupUserDecidableOptionVote(TimeStampedModel):
    group_decidable_option_access = models.ForeignKey(
        'decidables.GroupDecidableOptionAccess',
        related_name='group_user_decidable_option_vote',
        on_delete=models.CASCADE
    )
    group_user = models.ForeignKey(
        'group.GroupUser',
        related_name='group_user_decidable_option_vote',
        on_delete=models.CASCADE
    )
    value = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.group_decidable_option_access} - {self.group_user}: {self.value}'

 

