from rest_framework.routers import SimpleRouter
from flowback.group.viewsets.group import GroupViewSet
from flowback.group.viewsets.user import GroupUserViewSet
from flowback.group.viewsets.invite import GroupUserInvitationViewSet
from flowback.group.viewsets.invite import my_invites

from django.urls import path, include

urlpatterns = [
    path('invite/my-invites/',my_invites,name='my-invites')
]


router = SimpleRouter()
router.register(r'group',GroupViewSet,basename='group')
router.register(r"group/(?P<group_id>[^/.]+)/user",GroupUserViewSet,basename='group-user')
router.register(r"group/(?P<group_id>[^/.]+)/invite",GroupUserInvitationViewSet,basename='group-user-invitation')

urlpatterns += router.urls