import importlib

from django.urls import re_path

consumers = importlib.import_module("login.consumers")

websocket_urlpatterns = [
    re_path(r"^ws/extractor/(?P<congregation>[^/]+)/$", consumers.ExtractorConsumer),
]
