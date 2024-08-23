import django_filters
from flowback.user.models import User
from django.db.models import Q

class UserFilter(django_filters.FilterSet):
    user = django_filters.CharFilter(method='search_user')

    def search_user(self, queryset, name, value):
        name_query = Q()
        for term in value.split(' '):
            name_query |= Q(first_name__icontains=term) | Q(last_name__icontains=term)
        
        queryset = queryset.filter(
            Q(username__icontains=value)
            |
            Q(email__icontains=value)
            |
            name_query
        )
        return queryset
    

    class Meta:
        model = User
        fields = ['user']
        
