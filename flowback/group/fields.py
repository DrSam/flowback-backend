from django.db import models

class GroupUserInviteStatusChoices(models.TextChoices):
    PENDING = ("pending","Pending")
    ACCEPTED = ("accepted","Accepted")
    WITHDRAWN = ("withdrawn","Withdrawn")
    REJECTED = ("rejected","Rejected")