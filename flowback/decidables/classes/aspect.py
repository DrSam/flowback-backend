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

    def on_confirm(self):        
        pass

    def on_option_create(self, option):
        self.decidable.options.add(option)
        decidable_option = decidable_models.DecidableOption.objects.get(
            decidable=self.decidable,
            option=option
        )
        decidable_option.groups.set(self.decidable.get_root_decidable().groups.all())

            
