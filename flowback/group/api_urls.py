from rest_framework.routers import SimpleRouter
from flowback.group.viewsets.group import GroupViewSet
from flowback.group.viewsets.group_user import GroupUserViewSet



router = SimpleRouter()
router.register('group',GroupViewSet,basename='group')
router.register(r"group/(?P<group_id>[^/.]+)/user",GroupUserViewSet,basename='group-user')

urlpatterns = router.urls