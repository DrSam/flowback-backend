from rest_framework.routers import SimpleRouter
from flowback.group.viewsets.group import GroupViewSet
from flowback.group.viewsets.user import GroupUserViewSet
from flowback.group.viewsets.invite import GroupUserInvitationViewSet



router = SimpleRouter()
router.register('group',GroupViewSet,basename='group')
router.register(r"group/(?P<group_id>[^/.]+)/user",GroupUserViewSet,basename='group-user')
router.register(r"group/(?P<group_id>[^/.]+)/invite",GroupUserInvitationViewSet,basename='group-user-invitation')

urlpatterns = router.urls