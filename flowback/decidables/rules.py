import rules



@rules.predicate(bind=True)
def can_create_decidable(self,user_id,group_id):
    return True


@rules.predicate(bind=True)
def can_create_attachment(self,user_id,group_id):
    return True

@rules.predicate(bind=True)
def can_add_option(user,decidable):
    return True
