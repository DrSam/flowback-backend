from django.contrib import admin
from flowback.decidables.models import Decidable
from flowback.decidables.models import GroupDecidableAccess
from flowback.decidables.models import Attachment
from flowback.decidables.models import Option
from flowback.decidables.models import DecidableOption
from flowback.decidables.models import GroupDecidableOptionAccess
# from flowback.decidables.models import GroupDecidableAccess

admin.site.register(Attachment)
admin.site.register(Decidable)
admin.site.register(GroupDecidableAccess)
admin.site.register(GroupDecidableOptionAccess)
admin.site.register(DecidableOption)
admin.site.register(Option)
