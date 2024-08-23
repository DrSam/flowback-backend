from rest_framework.routers import SimpleRouter
from flowback.user.viewsets.user import UserViewSet


router = SimpleRouter()
router.register('user', UserViewSet, basename='user-management')

urlpatterns = router.urls