from .decidable_base import BaseDecidable


class Decidable(BaseDecidable):
    decidable_type = 'poll'
    
    def on_create(self):
        super().on_create()

    def on_confirm(self):
        from flowback.decidables.classes.option_base import BaseOption

        self.create_feed_channel()
        self.create_linkfile_poll()
        for option in self.decidable.options.all():
            option_class = BaseOption(option=option,decidable=self.decidable)
            option_class.create_linkfile_poll()
            option_class.create_reason_poll()
            option_class.create_feed_channel()
        
    def on_option_create(self, option):        
        from flowback.decidables.classes.option_base import BaseOption
        from flowback.decidables.classes.aspect import Decidable as AspectDecidable

        # In a vote, each reason has a linkfile poll and a reason poll
        option_class = BaseOption(option=option,decidable=self.decidable)
        option_class.create_linkfile_poll()
        option_class.create_reason_poll()
        option_class.create_feed_channel()

        for aspect in self.decidable.secondary_decidables.all():
            decidable_class = AspectDecidable(decidable=aspect)
            decidable_class.on_option_create(option)


