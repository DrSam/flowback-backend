from rest_framework.routers import SimpleRouter
from flowback.decidables.api_views import DecidableViewSet
from flowback.decidables.api_views import AttachmentViewSet
from flowback.decidables.api_views import OptionViewSet


router = SimpleRouter()
router.register(r"group/(?P<group_id>[^/.]+)/decidable",DecidableViewSet,basename='decidable')
router.register(r"group/(?P<group_id>[^/.]+)/attachment",AttachmentViewSet,basename='attachment')
router.register(r"group/(?P<group_id>[^/.]+)/decidable/(?P<decidable_id>[^/.]+)/option",OptionViewSet,basename='option')
urlpatterns = router.urls
