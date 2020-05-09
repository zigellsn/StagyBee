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
import json
import re
from contextlib import suppress

import aiohttp
from StagyBee.consumers import AsyncJsonRedisWebsocketConsumer
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from django.conf import settings
from django.shortcuts import get_object_or_404
from tenacity import retry, wait_random_exponential, stop_after_delay, retry_if_exception_type, RetryError

from picker.models import Credential

GLOBAL_TIMEOUT = {}


def generate_channel_group_name(function, congregation):
    con = re.sub(r'[^\x2D-\x2E\x30-\x39\x41-\x5A\x5F\x61-\x7A]', '_', congregation)
    return f"congregation.{function}.{con}"


class ExtractorConsumer(AsyncJsonRedisWebsocketConsumer):

    async def connect(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        await self.channel_layer.group_add(
            generate_channel_group_name("stage", congregation),
            self.channel_name
        )
        await self.accept()
        timeout = GLOBAL_TIMEOUT.get(congregation)
        if timeout is not None:
            timeout.cancel()
            GLOBAL_TIMEOUT.pop(congregation)
        await self.__connect_to_extractor(self.__get_redis_key(self.scope["url_route"]["kwargs"]["congregation"]))

    async def disconnect(self, close_code):
        if self.task is not None and not self.task.done():
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
        await self.channel_layer.group_discard(
            generate_channel_group_name("stage", self.scope["url_route"]["kwargs"]["congregation"]),
            self.channel_name
        )
        await self.__disconnect_from_extractor(self.__get_redis_key(self.scope["url_route"]["kwargs"]["congregation"]))
        raise StopConsumer()

    async def extractor_listeners(self, event):
        await self.__restart_waiter()
        await self.send_json(event["listeners"])

    async def extractor_status(self, event):
        await self.send_json(event["status"])

    async def encode_json(self, content):
        if type(content) == bytes:
            new_content = json.loads(content)
            if type(new_content) == dict:
                return json.dumps(new_content)
            return new_content
        else:
            return await super().encode_json(content=content)

    async def __waiter(self):
        await asyncio.sleep(settings.EXTRACTOR_TIMEOUT)
        reachable = await self.__get_extractor_status()
        if not reachable:
            await self.send_json("extractor_not_available")

    async def __restart_waiter(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        timeout = GLOBAL_TIMEOUT.get(congregation)
        if timeout is not None:
            timeout.cancel()
        GLOBAL_TIMEOUT[congregation] = asyncio.create_task(self.__waiter())

    @staticmethod
    def __get_redis_key(congregation):
        return f"stagybee::session:{generate_channel_group_name('stage', congregation)}"

    async def __get_extractor_status(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        credentials = await database_sync_to_async(get_object_or_404)(Credential, congregation=congregation)
        if credentials.touch:
            return
        if "session_id" in self.scope["url_route"]["kwargs"] and \
                self.scope["url_route"]["kwargs"]["session_id"] is not None:
            url = f"{self.extractor_url}api/status/{self.scope['url_route']['kwargs']['session_id']}/"
            try:
                self.task = asyncio.create_task(
                    self.__get_request(url))
                await self.task
            except aiohttp.ClientError:
                return False
            except RetryError:
                return False
            else:
                return True

    async def __connect_to_extractor(self, redis_key):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        credentials = await database_sync_to_async(get_object_or_404)(Credential, congregation=congregation)
        if credentials.touch:
            return
        self.extractor_url = credentials.extractor_url
        if not self.extractor_url.endswith("/"):
            self.extractor_url = self.extractor_url + "/"
        receiver_host = settings.RECEIVER_HOST
        if receiver_host == 0:
            receiver_host = self.scope['server'][1]
        receiver_port = settings.RECEIVER_PORT
        if receiver_port == 0:
            receiver_port = self.scope['server'][1]
        url = f"http://{receiver_host}:{receiver_port}/receiver/{congregation}/"
        if credentials.autologin is not None and credentials.autologin != "":
            payload = {"id": credentials.autologin, "url": url}
        else:
            payload = {"congregation": credentials.congregation,
                       "username": credentials.username,
                       "password": credentials.password,
                       "url": url}
        try:
            self.task = asyncio.create_task(self.__post_request(self.extractor_url + "api/subscribe/", payload))
            await self.task
        except aiohttp.ClientError:
            await self.send_json("extractor_not_available")
        except RetryError:
            await self.send_json("extractor_not_available")
        else:
            success = self.task.result()["success"]
            if success:
                self.scope["url_route"]["kwargs"]["session_id"] = self.task.result()["sessionId"]
                await self.send_json("subscribed_to_extractor")
            await self._redis.connect_uri(redis_key, self.channel_name)

    async def __disconnect_from_extractor(self, redis_key):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        credentials = await database_sync_to_async(get_object_or_404)(Credential, congregation=congregation)
        if credentials.touch:
            return
        if "session_id" in self.scope["url_route"]["kwargs"] and \
                self.scope["url_route"]["kwargs"]["session_id"] is not None:
            count = await self._redis.disconnect_uri(redis_key, self.channel_name)
            if count != 0:
                return
            try:
                self.task = asyncio.create_task(
                    self.__delete_request(
                        f"{self.extractor_url}api/unsubscribe/{self.scope['url_route']['kwargs']['session_id']}/"))
                await self.task
            except aiohttp.ClientError:
                await self.send_json("extractor_not_available")
            except RetryError:
                await self.send_json("extractor_not_available")
            else:
                success = self.task.result()["success"]
                if success:
                    await self.send_json("unsubscribed_from_extractor")
                    self.scope["url_route"]["kwargs"]["session_id"] = None

    @retry(retry=retry_if_exception_type(aiohttp.ClientError), wait=wait_random_exponential(multiplier=1, max=15),
           stop=stop_after_delay(15))
    async def __post_request(self, url, payload):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return await response.json()

    @retry(retry=retry_if_exception_type(aiohttp.ClientError), wait=wait_random_exponential(multiplier=1, max=15),
           stop=stop_after_delay(15))
    async def __delete_request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as response:
                return await response.json()

    @retry(retry=retry_if_exception_type(aiohttp.ClientError), wait=wait_random_exponential(multiplier=1, max=15),
           stop=stop_after_delay(15))
    async def __get_request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()


class ConsoleClientConsumer(AsyncJsonRedisWebsocketConsumer):

    async def connect(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        await self.channel_layer.group_add(
            generate_channel_group_name("console", congregation),
            self.channel_name
        )
        await self.accept()
        await self._redis.connect_uri(self.__get_redis_key(congregation), self.channel_name)

    async def disconnect(self, close_code):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        congregation_channel_group = generate_channel_group_name("console", congregation)
        count = await self._redis.disconnect_uri(self.__get_redis_key(congregation), self.channel_name)
        if count == 0:
            await self.channel_layer.group_send(congregation_channel_group, {"type": "exit"})
        await self.channel_layer.group_discard(congregation_channel_group, self.channel_name)
        raise StopConsumer()

    async def receive_json(self, text_data, **kwargs):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        congregation_channel_group = generate_channel_group_name("console", congregation)
        if "message" in text_data:
            await self.channel_layer.group_send(congregation_channel_group, {"type": "message", "message": text_data})

    async def alert(self, event):
        await self.send_json(event)

    async def timer(self, event):
        await self.send_json(event)

    async def message(self, event):
        await self.send_json(event)

    @staticmethod
    def __get_redis_key(congregation):
        return f"stagybee::console:{generate_channel_group_name('console', congregation)}"
