from django.db import models


class DecidableStateChoices(models.TextChoices):
    NOT_STARTED = ("not_started","Not started")
    OPEN = ("open","Open")
    CLOSED = ("closed","Closed")


class DecidableTypeChoices(models.TextChoices):
    POLL = ("poll","Poll")
    ASPECT = ("aspect","Aspect Poll")
    REASONPOLL = ("reason","Reason Poll")
    LINKFILEPOLL = ("linkfile","Link File Poll")
    VOTEPOLL = ("vote","Vote")
    CHALLENGE = ("challenge","Challenge")
    ELECTION = ("election","Election")


class VoteTypeChoices(models.TextChoices):
    SCORE = ("score","Score")
    PERCENTAGE = ("percentage","Percentage")
    APPROVAL = ("approval","Approval")
    NUMBER = ("number","Number")
    RATING = ("rating","Rating")


class VoteAggChoices(models.TextChoices):
    ADD = ("add","Add")


class AttachmentChoices(models.TextChoices):
    IMAGE = ("image","Image")
    FILE = ("file","File")
    LINK = ("link","Link")
