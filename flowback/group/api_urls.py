from rest_framework.routers import SimpleRouter
from .views.group import GroupViewSet
from .views.user import GroupUserViewSet

router = SimpleRouter()
router.register('group',GroupViewSet,basename='group')
router.register(r"(?P<group_id>[^/.]+)/group-user",GroupUserViewSet,basename='group-user')

urlpatterns = router.urls