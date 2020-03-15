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

import asyncio
from asyncio import CancelledError

import pytest
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.urls import re_path

from stopwatch.consumers import CentralTimerConsumer
from picker.tests import create_credential


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_central_timer_consumer():
    await database_sync_to_async(create_credential)()
    application = URLRouter([re_path(r"^ws/central_timer/(?P<congregation>[^/]+)/$", CentralTimerConsumer)])

    communicator = WebsocketCommunicator(application, "/ws/central_timer/LE/")
    connected, _ = await communicator.connect()
    assert connected
    await communicator.send_json_to(
        {"timer": "start", "duration": {"h": "0", "m": "0", "s": "5"}, "name": "abc", "index": 2})
    timer = False
    sync = False
    for i in range(5):
        try:
            response = await communicator.receive_json_from()
        except asyncio.TimeoutError:
            break
        except CancelledError:
            break
        if "mode" in response["timer"] and response["timer"]["mode"] == "started":
            assert response == {
                "timer": {"mode": "started", "name": "abc", "index": 2},
                "type": "timer"}
            timer = True
        else:
            assert "mode" in response["timer"]
            sync = True
        await asyncio.sleep(0.5)

    assert timer and sync

    await communicator.send_json_to({"timer": "stop"})
    assert await communicator.receive_json_from() == {"timer": {"mode": "stopped"}, "type": "timer"}

    await communicator.disconnect()
