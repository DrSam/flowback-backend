from rest_framework.routers import SimpleRouter
from flowback.user.views.user import UserViewSet


router = SimpleRouter()
router.register('user-management', UserViewSet, basename='user-management')

urlpatterns = router.urls