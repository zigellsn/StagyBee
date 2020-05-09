#  Copyright 2019-2020 Simon Zigelli
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
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.urls import re_path

from console.consumers import ConsoleConsumer
from stage.tests.test_consumers import get_or_create_credential


@pytest.fixture
def channel_layers():
    from django.conf import settings
    settings.CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        }
    }


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_console_consumer(channel_layers):
    test_user = await user()
    await database_sync_to_async(get_or_create_credential)()
    application = URLRouter([re_path(r"^ws/(?P<language>[^/]+)/console/(?P<congregation>[^/]+)/$", ConsoleConsumer)])
    communicator = WebsocketCommunicator(application, "/ws/de/console/LE/")
    communicator.scope['user'] = test_user
    connected, _ = await communicator.connect()
    assert connected
    response = await communicator.receive_json_from()
    assert response["type"] == "times"
    await communicator.send_json_to({"alert": {"message": "Bla"}})
    response = await communicator.receive_json_from()
    assert response == {"alert": {"alert": {"message": "Bla"}}, "type": "alert"}
    await communicator.disconnect()


@database_sync_to_async
def user():
    return get_user_model().objects.create_user("testuser", "12345")
