from rest_framework.routers import SimpleRouter
from .views.group import GroupViewSet

router = SimpleRouter()
router.register('group',GroupViewSet,basename='group')

urlpatterns = router.urls