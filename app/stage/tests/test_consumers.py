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

import pytest
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator, HttpCommunicator
from django.urls import re_path

from picker.models import Credential
from stage.consumers import ExtractorConsumer, MessageConsumer, generate_channel_group_name


@pytest.fixture
def channel_layers():
    from django.conf import settings
    settings.CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        }
    }


def get_or_create_credential(congregation='LE', autologin='abc', username='abc', password='abc', display_name='The LE',
                             extractor_url='www.abc.com', touch=False):
    return Credential.objects.get_or_create(congregation=congregation, autologin=autologin,
                                            username=username, password=password, display_name=display_name,
                                            extractor_url=extractor_url, touch=touch)


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_extractor_consumer(channel_layers):
    await database_sync_to_async(get_or_create_credential)()
    application = URLRouter(
        [re_path(r"^ws/(?P<language>[^/]+)/extractor/(?P<congregation>[^/]+)/$", ExtractorConsumer.as_asgi())])

    communicator = WebsocketCommunicator(application, "/ws/de/extractor/LE/")
    communicator.scope["server"] = ["www", 8000]
    connected, _ = await communicator.connect()
    assert connected
    # await communicator.send_json_to({"hello": "hello"})
    # response = await communicator.receive_json_from()
    # assert response == {"hello": "hello"}
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_console_client_consumer(channel_layers):
    await database_sync_to_async(get_or_create_credential)()
    application = URLRouter(
        [re_path(r"^ws/(?P<language>[^/]+)/message/(?P<congregation>[^/]+)/$", MessageConsumer.as_asgi())])

    communicator = HttpCommunicator(application, "GET", "/ws/de/message/LE/")
    stage_group_name = generate_channel_group_name("message", "LE")
    await get_channel_layer().group_send(stage_group_name, {"type": "message.alert", "alert": {"value": "Bla"}})
    response = await communicator.receive_nothing()
    assert response
    # await communicator.send_json_to({"hello": "hello"})
    # response = await communicator.receive_json_from()
    # assert response == {"hello": "hello"}
    # await communicator.disconnect()
