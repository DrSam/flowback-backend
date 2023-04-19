"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from backend.settings import DEBUG, MEDIA_URL, MEDIA_ROOT, URL_SUBPATH
from flowback.poll.views import PollUserScheduleListAPI, PollListApi
from flowback.user.urls import user_patterns
from flowback.group.urls import group_patterns
from flowback.poll.urls import group_poll_patterns, poll_patterns
from flowback.chat.urls import chat_patterns
from flowback.notification.urls import notification_patterns
from django.conf.urls.static import static
from graphqlPlugin.urls import urlpatterns as up

api_urlpatterns = [
    path('', include((user_patterns, 'user'))),
    path('group/', include((group_patterns, 'group'))),
    path('chat/', include((chat_patterns, 'chat'))),
    path('group/<int:group>/poll/', include((group_poll_patterns, 'group_poll'))),
    path('group/poll/', include((poll_patterns, 'poll'))),
    path('notification/', include((notification_patterns, 'notification'))),
    path('home/polls', PollListApi.as_view(), name='home_polls'),
    path('poll/user/schedule', PollUserScheduleListAPI.as_view(), name='poll_user_schedule'),
    path('graphql/', include((up, 'graphql_plugin')))
]

urlpatterns = [
    path(f'{URL_SUBPATH}/' if URL_SUBPATH else '', include((api_urlpatterns, 'api'))),
    path('admin/', admin.site.urls, name='admin')
]

if DEBUG:
    urlpatterns += static((f'/{URL_SUBPATH}' if URL_SUBPATH else '') + MEDIA_URL,
                          document_root=MEDIA_ROOT)
