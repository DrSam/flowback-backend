import django_filters
from flowback.group.models import Group
from flowback.group.models import GroupUser


class GroupFilter(django_filters.FilterSet):
    name__icontains = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = Group
        fields = ['name','name__icontains','chat','direct_join','group_folder']



class GroupUserFilter(django_filters.FilterSet):
    user_contains = django_filters.CharFilter(lookup_expr='icontains',field_name='user__username')
    user_startswith = django_filters.CharFilter(lookup_expr='istartswith',field_name='user__username')

    class Meta:
        model = GroupUser
        fields = ['is_admin','user_contains','user_startswith']
