from rest_framework.routers import SimpleRouter
from feed.viewset import MessageViewSet


router = SimpleRouter()
router.register(r"channel/(?P<channel_id>[^/.]+)/message",MessageViewSet,basename='message')
urlpatterns = router.urls
