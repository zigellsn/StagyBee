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
import aioredis
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from decouple import config
from django.conf import settings
from django.shortcuts import get_object_or_404
from tenacity import retry, wait_random_exponential, stop_after_delay, retry_if_exception_type, RetryError

from picker.models import Credential


def generate_channel_group_name(congregation):
    return "congregation.%s" % re.sub(r'[^\x2D-\x2E\x30-\x39\x41-\x5A\x5F\x61-\x7A]', '_', congregation)


class ExtractorConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.congregation = self.scope["url_route"]["kwargs"]["congregation"]
        self.redis_key = "stagybee:session:%s" % generate_channel_group_name(self.congregation)
        self.credentials = None
        self.sessionId = None
        self.extractor_url = ""
        self.task = None

    async def connect(self):
        await self.channel_layer.group_add(
            generate_channel_group_name(self.congregation),
            self.channel_name
        )
        await self.accept()
        await self.connect_to_extractor()

    async def disconnect(self, close_code):
        if self.task is not None and not self.task.done():
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
        await self.channel_layer.group_discard(
            generate_channel_group_name(self.congregation),
            self.channel_name
        )
        await self.disconnect_from_extractor()
        raise StopConsumer()

    async def extractor_listeners(self, event):
        await self.send_json("subscribed_to_extractor")
        await self.send_json(event["listeners"])

    async def encode_json(self, content):
        if type(content) == bytes:
            new_content = json.loads(content)
            if type(new_content) == dict:
                return json.dumps(new_content)
            return new_content
        else:
            return await super().encode_json(content=content)

    async def connect_to_extractor(self):
        self.credentials = await database_sync_to_async(get_object_or_404)(Credential,
                                                                           congregation=self.congregation)
        if self.credentials.touch:
            return
        self.extractor_url = self.credentials.extractor_url
        if not self.extractor_url.endswith("/"):
            self.extractor_url = self.extractor_url + "/"
        url = "http://%s:%s/receiver/%s/" % (config("RECEIVER_HOST", default=self.scope["server"][0]),
                                             config("RECEIVER_PORT", default=self.scope["server"][1]),
                                             self.congregation)
        if self.credentials.autologin is not None:
            payload = {"id": self.credentials.autologin, "url": url}
        else:
            payload = {"congregation": self.credentials.congregation,
                       "username": self.credentials.username,
                       "password": self.credentials.password,
                       "url": url}
        try:
            self.task = asyncio.create_task(self.post_request(self.extractor_url + "api/subscribe/", payload))
            await self.task
        except aiohttp.ClientError:
            await self.send_json("extractor_not_available")
        except RetryError:
            await self.send_json("extractor_not_available")
        else:
            success = self.task.result()["success"]
            if success:
                self.sessionId = self.task.result()["sessionId"]
                await self.send_json("subscribed_to_extractor")
        await connect_uri(self.redis_key, self.channel_name)

    async def disconnect_from_extractor(self):
        if self.credentials.touch:
            return
        if self.sessionId is not None:
            count = await disconnect_uri(self.redis_key, self.channel_name)
            if count != 0:
                return
            try:
                self.task = asyncio.create_task(
                    self.delete_request(self.extractor_url + "api/unsubscribe/%s/" % self.sessionId))
                await self.task
            except aiohttp.ClientError:
                await self.send_json("extractor_not_available")
            except RetryError:
                await self.send_json("extractor_not_available")
            else:
                success = self.task.result()["success"]
                if success:
                    await self.send_json("unsubscribed_from_extractor")
                    self.sessionId = None

    @retry(retry=retry_if_exception_type(aiohttp.ClientError), wait=wait_random_exponential(multiplier=1, max=15),
           stop=stop_after_delay(15))
    async def post_request(self, url, payload):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return await response.json()

    @retry(retry=retry_if_exception_type(aiohttp.ClientError), wait=wait_random_exponential(multiplier=1, max=15),
           stop=stop_after_delay(15))
    async def delete_request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as response:
                return await response.json()


class ConsoleClientConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.congregation = self.scope["url_route"]["kwargs"]["congregation"]
        self.redis_key = "stagybee:console:%s" % generate_channel_group_name(self.congregation)

    async def connect(self):
        await self.channel_layer.group_add(
            generate_channel_group_name(self.scope["url_route"]["kwargs"]["congregation"]),
            self.channel_name
        )
        await connect_uri(self.redis_key, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            generate_channel_group_name(self.scope["url_route"]["kwargs"]["congregation"]),
            self.channel_name
        )
        await disconnect_uri(self.redis_key, self.channel_name)
        raise StopConsumer()

    async def alert(self, event):
        await self.send_json(event)


async def connect_uri(group, channel_name):
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
    redis = await aioredis.create_redis(host)
    await redis.sadd(group, channel_name)
    await redis.expire(group, config("REDIS_EXPIRATION", default=21600))
    redis.close()
    await redis.wait_closed()


async def disconnect_uri(group, channel_name):
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
    redis = await aioredis.create_redis(host)
    await redis.srem(group, channel_name)
    count = await redis.scard(group)
    redis.close()
    await redis.wait_closed()
    return count
