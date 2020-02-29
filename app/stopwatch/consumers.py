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

from channels.exceptions import StopConsumer

from stagy_bee.consumers import AsyncJsonRedisWebsocketConsumer
from stage.consumers import generate_channel_group_name


class TimerConsumer(AsyncJsonRedisWebsocketConsumer):

    async def connect(self):
        await self.channel_layer.group_add(
            generate_channel_group_name("console", self.scope["url_route"]["kwargs"]["congregation"]),
            self.channel_name
        )
        await self.accept()
        message = await self._redis.connect_timer(
            self.__get_redis_key(self.scope["url_route"]["kwargs"]["congregation"]))
        if message is not None:
            await self.send_json(message)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            generate_channel_group_name("console", self.scope["url_route"]["kwargs"]["congregation"]),
            self.channel_name
        )
        raise StopConsumer()

    async def receive_json(self, text_data, **kwargs):
        congregation_group_name = generate_channel_group_name("console",
                                                              self.scope["url_route"]["kwargs"]["congregation"])
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

    @staticmethod
    def __get_redis_key(congregation):
        return f"stagybee::timer:{generate_channel_group_name('console', congregation)}"
