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
import asyncio
from datetime import datetime

from channels.exceptions import StopConsumer

from settings import DATETIME_FORMAT
from stage.consumers import generate_channel_group_name
from stagy_bee.consumers import AsyncJsonRedisWebsocketConsumer


class CentralTimerConsumer(AsyncJsonRedisWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._timer = None

    async def connect(self):
        await self.channel_layer.group_add(
            generate_channel_group_name("timer", self.scope["url_route"]["kwargs"]["congregation"]),
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            generate_channel_group_name("timer", self.scope["url_route"]["kwargs"]["congregation"]),
            self.channel_name
        )
        raise StopConsumer()

    async def timeout_callback(self, name, context, _):
        congregation_group_name = generate_channel_group_name("timer",
                                                              self.scope["url_route"]["kwargs"]["congregation"])
        start = datetime.strptime(context["start"], DATETIME_FORMAT)
        delta = datetime.now() - start
        await self.channel_layer.group_send(congregation_group_name,
                                            {"timer": {"sync": get_json_duration(delta.seconds),
                                                       "duration": context["duration"],
                                                       "name": name, "index": context["index"]}, "type": "timer"})

    async def receive_json(self, text_data, **kwargs):
        congregation_group_name = generate_channel_group_name("timer",
                                                              self.scope["url_route"]["kwargs"]["congregation"])
        if "timer" not in text_data:
            return
        if text_data["timer"] == "start":
            await self.channel_layer.group_send(congregation_group_name,
                                                {"timer": {"timer": "started", "name": text_data["name"],
                                                           "index": text_data["index"]}, "type": "timer"})
            if self._timer is None:
                context = {"duration": text_data["duration"],
                           "start": datetime.now().strftime(DATETIME_FORMAT),
                           "index": text_data["index"]}
                self._timer = Timer(1, self.timeout_callback, context=context, timer_name=text_data["name"])
        elif text_data["timer"] == "stop":
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            await self.channel_layer.group_send(congregation_group_name,
                                                {"timer": {"timer": "stopped"}, "type": "timer"})

    async def timer(self, event):
        await self.send_json(event)


class Timer:
    def __init__(self, interval, callback, first_immediately=True, timer_name="timer", context=None):
        self._interval = interval
        self._first_immediately = first_immediately
        self._callback = callback
        self._name = timer_name
        self._context = context
        self._is_first_call = True
        self._running = True
        self._task = asyncio.create_task(self._job())

    async def _job(self):
        try:
            while self._running:
                if not self._is_first_call or not self._first_immediately:
                    await asyncio.sleep(self._interval)
                await self._callback(self._name, self._context, self)
                self._is_first_call = False
            self._running = False
        except Exception as ex:
            print(ex)

    def cancel(self):
        self._running = False
        self._task.cancel()


def get_duration(duration):
    return int(duration["h"]) * 3600 + int(duration["m"]) * 60 + int(duration["s"])


def get_json_duration(duration):
    return {"h": int(duration / 3600), "m": int((duration % 3600) / 60), "s": (duration % 3600) % 60}
