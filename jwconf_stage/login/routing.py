from django.urls import re_path

import consumers

websocket_urlpatterns = [
    re_path(r'^ws/extractor/(?P<congregation>[^/]+)/$', consumers.ExtractorConsumer),
]
