from .decidable_base import BaseDecidable
from flowback.decidables import models as decidable_models

class Decidable(BaseDecidable):
    decidable_type = 'aspect'
    
    def on_create(self):
        super().on_create()
        # Add options of primary decidable to this decidable
        self.decidable.options.set(self.decidable.primary_decidable.options.all())

        # Add to all groups in primary decidable
        for option in self.decidable.options.all():
            decidable_option = decidable_models.DecidableOption.objects.get(
                decidable=self.decidable,
                option=option
            )
            decidable_option.groups.set(self.decidable.get_root_decidable().groups.all())
        
        self.create_feed_channel()

    def on_confirm(self):        
        pass

    def on_option_create(self, option):
        self.decidable.options.add(option)
        decidable_option = decidable_models.DecidableOption.objects.get(
            decidable=self.decidable,
            option=option
        )
        decidable_option.groups.set(self.decidable.get_root_decidable().groups.all())

    
    def create_feed_channel(self):
        for group_decidable_access in self.decidable.group_decidable_access.all():
            primary_group_decidable_access = self.decidable.primary_decidable.group_decidable_access.get(
                group=group_decidable_access.group
            )
            channel = primary_group_decidable_access.feed_channel

            group_decidable_access.feed_channel = channel
            group_decidable_access.save()
