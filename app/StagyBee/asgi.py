#  Copyright 2019-2025 Simon Zigelli
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import re_path

django.setup()

from console import routing as console_routing
from stage import routing as stage_routing

urlpatterns = stage_routing.websocket_urlpatterns + console_routing.urlpatterns
http_urlpatterns = stage_routing.http_urlpatterns + [re_path(r'', get_asgi_application())]

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "StagyBee.settings")
application = ProtocolTypeRouter({
    "http": AuthMiddlewareStack(URLRouter(http_urlpatterns)),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(urlpatterns)
        ),
    )
})
