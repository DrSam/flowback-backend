import rules
from django.db.models.fields import BooleanField

# Built in predicates
is_superuser = rules.predicates.is_superuser

# Our group predicates
@rules.predicate
def is_admin(user,group):
    from flowback.group.models import GroupUser

    group_user = is_admin.context.get('user_group')
    if not group_user:
        group_user = GroupUser.objects.get(
            user=user,
            group=group
        )
    
    is_admin.context['group_user'] = group_user
    
    return group_user.is_admin


@rules.predicate
def is_creator(user,group):
    from flowback.group.models import GroupUser
    group_user = is_creator.context.get('user_group')
    if not group_user:
        group_user = GroupUser.objects.get(
            user=user,
            group=group
        )
    
    is_creator.context['group_user'] = group_user

    return group_user.group.created_by == group_user.user


@rules.predicate
def is_group_user(user,group):
    from flowback.group.models import GroupUser
    return GroupUser.objects.filter(
        user=user,
        group=group
    ).exists()


# Group permission based predicates
def group_permission_predicates(field_name):
    @rules.predicate
    def group_pred(user,group):
        from flowback.group.models import GroupUser
        
        group_user = group_pred.context.get('user_group')
        if not group_user:
            group_user = GroupUser.objects.get(
                user=user,
                group=group
            )

        group_pred.context['group_user'] = group_user

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
