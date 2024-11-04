from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularRedocView, SpectacularAPIView
from rest_framework import permissions
from rest_framework.schemas import get_schema_view

from backend.settings import DEBUG, MEDIA_URL, MEDIA_ROOT, URL_SUBPATH, INTEGRATIONS, STATIC_ROOT, STATIC_URL
from flowback.poll.views.poll import PollUserScheduleListAPI, PollListApi
from flowback.user.urls import user_patterns
from flowback.group.urls import group_patterns
from flowback.poll.urls import group_poll_patterns, poll_patterns
from flowback.chat.urls import chat_patterns
from flowback.notification.urls import notification_patterns
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

api_urlpatterns = [
    path('', include((user_patterns, 'user'))),
    path('user-management/', include('flowback.user.api_urls')),
    path('group/', include((group_patterns, 'group'))),
    path('group-management/',include('flowback.group.api_urls')),
    path('chat/', include((chat_patterns, 'chat'))),
    path('group/<int:group_id>/poll/', include((group_poll_patterns, 'group_poll'))),
    path('group/poll/', include((poll_patterns, 'poll'))),
    path('notification/', include((notification_patterns, 'notification'))),

    path('home/polls', PollListApi.as_view(), name='home_polls'),
    path('poll/user/schedule', PollUserScheduleListAPI.as_view(), name='poll_user_schedule'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('decidable-management/', include('flowback.decidables.api_urls')),
    path('feed/',include('feed.api_urls')),
]

if INTEGRATIONS:
    try:
        from flowback_addon.urls import addon_patterns
        api_urlpatterns.append(path('', include((addon_patterns, 'addon'))))

    except ModuleNotFoundError:
        pass

    except Exception as e:
        raise e

urlpatterns = [
    path(f'{URL_SUBPATH}/' if URL_SUBPATH else '', include((api_urlpatterns, 'api'))),
    path('admin/', admin.site.urls, name='admin')
]

if DEBUG:
    urlpatterns += static((f'/{URL_SUBPATH}' if URL_SUBPATH else '') + MEDIA_URL,
                          document_root=MEDIA_ROOT)
    urlpatterns += static((f'/{URL_SUBPATH}' if URL_SUBPATH else '') + STATIC_URL,
                          document_root=STATIC_ROOT)
