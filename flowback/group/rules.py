import rules
from django.db.models.fields import BooleanField

# Built in predicates
is_superuser = rules.predicates.is_superuser

# Our group predicates
@rules.predicate(bind=True)
def is_admin(self, user,group):
    from flowback.group.models import GroupUser
    group_user = self.context.get('user_group')
    if not group_user:
        group_user = GroupUser.objects.filter(
            user=user,
            group=group
        ).first()
        if not group_user:
            return False
    
    self.context['group_user'] = group_user
    
    return group_user.is_admin


@rules.predicate(bind=True)
def is_creator(self,user,group):
    from flowback.group.models import GroupUser
    group_user = self.context.get('user_group')
    if not group_user:
        group_user = GroupUser.objects.filter(
            user=user,
            group=group
        ).first()
        if not group_user:
            return False
    
    self.context['group_user'] = group_user

    return group_user.group.created_by == group_user.user


@rules.predicate(bind=True)
def is_group_user(self,user,group):
    from flowback.group.models import GroupUser
    return GroupUser.objects.filter(
        user=user,
        group=group
    ).exists()


# Group permission based predicates
def group_permission_predicates(field_name):
    @rules.predicate(bind=True)
    def group_pred(self,user,group):
        from flowback.group.models import GroupUser
        
        group_user = self.context.get('user_group')
        if not group_user:
            group_user = GroupUser.objects.filter(
                user=user,
                group=group
            ).first()
            if not group_user:
                return False

        self.context['group_user'] = group_user

        if group_user.permission:
            field = group_user.permission.__class__._meta.get_field(field_name)
            if not isinstance(field,BooleanField):
                return False
            return getattr(group_user.permission,field_name)
        
        elif group.default_permission:
            field = group.default_permission.__class__._meta.get_field(field_name)
            if not isinstance(field,BooleanField):
                return False
            return getattr(group.default_permission,field_name)
        
        else:
            return False
    
    return group_pred


# Complex predicates
is_group_admin = is_superuser | is_admin | is_creator
is_group_creator = is_superuser | is_creator
