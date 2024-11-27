from django.db.models.signals import post_save
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from flowback.decidables.models import Decidable
from flowback.decidables.models import Option

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
