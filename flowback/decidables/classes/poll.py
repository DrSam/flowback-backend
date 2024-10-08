from .base import BaseDecidable
from rest_framework.exceptions import ValidationError

class Decidable(BaseDecidable):
    pass

    def validate_vote_value(self, value):
        if value not in [-1,0,1]:
            raise ValidationError('Invalid voting value')
        
    def vote(self,option,value):
        self.validate_vote_value(value)
        # Cast vote here
        