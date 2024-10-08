import django_filters
from flowback.decidables import models as decidable_models


class DecidableFilter(django_filters.FilterSet):
    title_contains = django_filters.CharFilter(lookup_expr='icontains',field_name='title')
    title_startswith = django_filters.CharFilter(lookup_expr='istartswith',field_name='title')

    class Meta:
        model = decidable_models.Decidable
        fields = ['title_contains','title_startswith']


class OptionFilter(django_filters.FilterSet):
    title_contains = django_filters.CharFilter(lookup_expr='icontains',field_name='title')
    title_startswith = django_filters.CharFilter(lookup_expr='istartswith',field_name='title')

    class Meta:
        model = decidable_models.Option
        fields = ['title_contains','title_startswith']

