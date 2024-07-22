import django_filters
from flowback.group.models import Group


class GroupFilter(django_filters.FilterSet):
    name__icontains = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = Group
        fields = ['name','name__icontains','chat','direct_join','group_folder']
