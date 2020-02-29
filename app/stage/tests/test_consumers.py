#  Copyright 2019 Simon Zigelli
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
from django.urls import re_path

from consumers import ExtractorConsumer, ConsoleClientConsumer
from picker.tests import create_credential


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_extractor_consumer():
    await database_sync_to_async(create_credential)()
    application = URLRouter([re_path(r"^ws/extractor/(?P<congregation>[^/]+)/$", ExtractorConsumer)])

    communicator = WebsocketCommunicator(application, "/ws/extractor/LE/")
    communicator.scope["server"] = ["www", 8000]
    connected, _ = await communicator.connect()
    assert connected
    # await communicator.send_json_to({"hello": "hello"})
    # response = await communicator.receive_json_from()
    # assert response == {"hello": "hello"}
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_console_client_consumer():
    application = URLRouter([re_path(r"^ws/console_client/(?P<congregation>[^/]+)/$", ConsoleClientConsumer)])

    communicator = WebsocketCommunicator(application, "/ws/console_client/LE/")
    connected, _ = await communicator.connect()
    assert connected
    # await communicator.send_json_to({"hello": "hello"})
    # response = await communicator.receive_json_from()
    # assert response == {"hello": "hello"}
    await communicator.disconnect()
