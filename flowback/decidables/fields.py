from django.db import models


class DecidableStateChoices(models.TextChoices):
    NOT_STARTED = ("not_started","Not started")
    OPEN = ("open","Open")
    CLOSED = ("closed","Closed")


class DecidableTypeChoices(models.TextChoices):
    POLL = ("poll","Poll")
    REASONPOLL = ("reasonpoll","Reason Poll")
    LINKFILEPOLL = ("linkfilepoll","Link File Poll")
    VOTEPOLL = ("votepoll","Vote poll")
    CHALLENGE = ("challenge","Challenge")
    ELECTION = ("election","Election")


class VoteTypeChoices(models.TextChoices):
    APPROVAL = ("approval","Approval")
    SCORE = ("score","Score")


class VoteAggChoices(models.TextChoices):
    ADD = ("add","Add")


class AttachmentChoices(models.TextChoices):
    IMAGE = ("image","Image")
    FILE = ("file","File")
    LINK = ("link","Link")
