from .decidable_base import BaseDecidable



class Decidable(BaseDecidable):
    decidable_type = 'poll'
    
    def on_create(self):
        super().on_create()

    def on_confirm(self):        
        self.create_feed_channel()
            
    def on_option_create(self, option):
        pass