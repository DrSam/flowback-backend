
from flowback.group.models import Group
from flowback.group.models import GroupUser
from rest_framework import viewsets
import django_filters
from rest_framework.permissions import BasePermission
from flowback.group.filters import GroupUserFilter
from flowback.group.serializers import GroupUserSerializer



class GroupUserViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)


class GroupUserViewSet(
    viewsets.ModelViewSet
):
    _group = None

    serializer_class = GroupUserSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = GroupUserFilter
    permission_classes = [GroupUserViewSetPermission]


    def get_queryset(self):
        return GroupUser.objects.filter(
            active=True,
            group=self.get_group()
        )
    
    def get_group(self):
        if self._group:
            return self._group
        
        group_id = self.kwargs.get('group_id')
        group = Group.objects.get(id=group_id)
        self._group = group
        return self._group
