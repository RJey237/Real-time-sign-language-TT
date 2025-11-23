"""
ASGI config for rtslt project with Django Channels.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rtslt.settings')

django_asgi_app = get_asgi_application()

from translator.routing import websocket_urlpatterns  # import AFTER settings/app initialized

application = ProtocolTypeRouter({
	'http': django_asgi_app,
	'websocket': AllowedHostsOriginValidator(
		AuthMiddlewareStack(
			URLRouter(websocket_urlpatterns)
		)
	),
})
