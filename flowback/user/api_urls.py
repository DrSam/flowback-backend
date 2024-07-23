from rest_framework.routers import SimpleRouter
from flowback.user.views.user import UserViewSet
from flowback.user.views.user import BlockedUserViewSet


router = SimpleRouter()
router.register('user-management', UserViewSet, basename='user-management')
router.register('blocked-users', BlockedUserViewSet, basename='blocked-user')

urlpatterns = router.urls