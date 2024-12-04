from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from flowback.decidables.models import Decidable
from flowback.decidables.models import Option
from flowback.decidables.models import GroupUserDecidableOptionVote
from flowback.decidables.models import GroupDecidableOptionAccess

@receiver(m2m_changed, sender=Decidable)
def set_decidable_root(sender, instance, created, **kwargs):
    if not created:
        return
    
    if instance.primary_decidable:
        instance.root_decidable = instance.primary_decidable.get_root_decidable()
        instance.save()
    elif instance.parent_decidable:
        instance.root_decidable = instance.parent_decidable.get_root_decidable()
        instance.save()
    elif instance.parent_option:
        instance.root_decidable = instance.parent_option.root_decidable
        instance.save()


@receiver(post_save, sender=Option)
def reset_option_votes(sender, instance, created, **kwargs):
    # All votes for an option are reset when any change is made
    GroupUserDecidableOptionVote.objects.filter(
        group_decidable_option_access__decidable_option__option=instance
    ).delete()

    GroupDecidableOptionAccess.objects.filter(
        decidable_option__option=instance
    ).update(
        value=0,
        quorum=0,
        approval=0
    )

@receiver(pre_delete, sender=Decidable)
def cascade_deletion(sender, instance, **kwargs):
    if instance.primary_decidable:
        return
    for option in instance.options.all():
        option.delete()
