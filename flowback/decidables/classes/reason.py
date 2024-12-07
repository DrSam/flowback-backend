from .decidable_base import BaseDecidable



class Decidable(BaseDecidable):
    decidable_type = 'poll'
    
    def on_create(self):
        super().on_create()
        if self.decidable.parent_option:
            self.decidable.feed_channel_id = self.parent_option.feed_channel_id
            self.decidable.save()
        if self.decidable.parent_decidable:
            self.decidable.feed_channel_id = self.parent_decidable.feed_channel_id
            self.decidable.save()

    def on_confirm(self):        
        pass
            
    def on_option_create(self, option):
        pass