from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/asl/$', consumers.ASLConsumer.as_asgi()),
    re_path(r'^ws/chat/(?P<target_id>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'^ws/video/(?P<target_id>[^/]+)/$', consumers.VideoConsumer.as_asgi()),
]