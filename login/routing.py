from django.urls import re_path

from login.consumers import ExtractorConsumer

websocket_urlpatterns = [
    re_path(r"^ws/extractor/(?P<congregation>[^/]+)/$", ExtractorConsumer),
]
