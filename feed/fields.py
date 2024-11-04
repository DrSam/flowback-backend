from django.db import models


class ChannelTypechoices(models.TextChoices):
    PRIVATE = ("private","Private")
    GROUP = ("group","Group")
    DECIDABLE = ("decidable","Decidable")
    OPTION = ("option","Option")