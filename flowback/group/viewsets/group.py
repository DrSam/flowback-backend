
from flowback.group.models import Group
from flowback.group.models import GroupUser
from rest_framework import viewsets
from rest_framework import mixins
from flowback.group.serializers import GroupSerializer
import django_filters
from flowback.group.filters import GroupFilter
from rest_framework.permissions import BasePermission



class GroupViewSetPermission(BasePermission):
    def has_permission(self, request, view):
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)

class GroupViewSet(
    viewsets.ModelViewSet
):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = GroupFilter
    permission_classes = [GroupViewSetPermission]

    permission_type_map = {
        "partial_update": "change",
        "retrieve":"view"
    }
    
