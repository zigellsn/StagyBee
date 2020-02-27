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

from stopwatch.consumers import TimerConsumer


@pytest.mark.asyncio
async def test_stopwatch_consumer():
    application = URLRouter([re_path(r"^ws/timer/(?P<congregation>[^/]+)/$", TimerConsumer)])

    communicator = WebsocketCommunicator(application, "/ws/timer/LE/")
    connected, _ = await communicator.connect()
    assert connected
    await communicator.send_json_to({"alert": "timer"})
    response = await communicator.receive_json_from()
    assert response == {"alert": {"alert": "timer"}, "type": "alert"}
    await communicator.send_json_to({"timer": "start"})
    response = await communicator.receive_json_from()
    assert response == {"alert": {"alert": "message"}, "type": "alert"}
    await communicator.disconnect()
