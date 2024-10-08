class BaseDecidable:
    group = None
    decidable = None

    def __init__(self,group,decidable):
        self.group = group
        self.decidable = decidable
    
    def validate_vote_value(self,value):
        raise NotImplementedError('Vote validation method not implemented')

    def vote(self,option,value):
        raise NotImplementedError('Vote method not implemented')
    
