from .decidable_base import BaseDecidable



class Decidable(BaseDecidable):
    decidable_type = 'poll'
    
    def on_create(self):
        super().on_create()

    def on_confirm(self):        
        
        # Create channel only if not a sub poll
        if not (self.decidable.parent_decidable or self.decidable.primary_decidable):
            self.create_feed_channel()
            
    def on_option_create(self, option):
        pass