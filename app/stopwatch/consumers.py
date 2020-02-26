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

import json

from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from stage.consumers import generate_channel_group_name
from .timer_redis import connect_timer


class TimerConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.congregation = self.scope["url_route"]["kwargs"]["congregation"]
        self.redis_key = f"stagybee::timer:{generate_channel_group_name('console', self.congregation)}"

    async def connect(self):
        await self.channel_layer.group_add(
            generate_channel_group_name("console", self.congregation),
            self.channel_name
        )
        await self.accept()
        await connect_timer(self, self.redis_key)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            generate_channel_group_name("console", self.congregation),
            self.channel_name
        )
        raise StopConsumer()

    async def receive_json(self, text_data, **kwargs):
        congregation_group_name = generate_channel_group_name("console", self.congregation)
        if "alert" in text_data:
            await self.channel_layer.group_send(congregation_group_name, {"type": "alert", "alert": text_data})
        else:
            await self.channel_layer.group_send(congregation_group_name, {"type": "timer", "timer": text_data})

    async def exit(self, event):
        await self.send_json(event)

    async def timer(self, event):
        await self.send_json(event)

    async def alert(self, event):
        await self.send_json(event)
