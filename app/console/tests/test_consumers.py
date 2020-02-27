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
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.urls import re_path

from console.consumers import ConsoleConsumer


@pytest.mark.asyncio
async def test_console_consumer():
    application = URLRouter([re_path(r"^ws/(?P<language>[^/]+)/console/(?P<congregation>[^/]+)/$", ConsoleConsumer)])

    communicator = WebsocketCommunicator(application, "/ws/de/console/LE/")
    connected, _ = await communicator.connect()
    assert connected
    # await communicator.send_to(text_data="hello")
    # response = await communicator.receive_from()
    # assert response == "hello"
    await communicator.disconnect()
