import asyncio
import importlib
import json
from contextlib import suppress

import aiohttp
import aioredis
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.shortcuts import get_object_or_404
from tenacity import retry, stop_after_attempt, retry_if_exception_type, RetryError

picker = importlib.import_module("picker.models")


class ExtractorConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.congregation = self.scope["url_route"]["kwargs"]["congregation"]
        self.congregation_group_name = "congregation.%s" % self.congregation
        self.credentials = None
        self.sessionId = None
        self.extractor_url = ""
        self.task = None

    async def connect(self):
        await self.channel_layer.group_add(
            self.congregation_group_name,
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
            self.congregation_group_name,
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
        self.credentials = await database_sync_to_async(get_object_or_404)(picker.Credential,
                                                                           congregation=self.congregation)
        self.extractor_url = self.credentials.extractor_url
        if not self.extractor_url.endswith("/"):
            self.extractor_url = self.extractor_url + "/"
        url = "http://localhost:8000/receiver/%s/" % self.congregation
        if self.credentials.autologin is not None:
            payload = {"id": self.credentials.autologin, "url": url}
        else:
            payload = {"congregation": self.credentials.congregation,
                       "username": self.credentials.username,
                       "password": self.credentials.password,
                       "url": url}
        try:
            self.task = asyncio.create_task(self.post_request(self.extractor_url + "api/subscribe", payload))
            await self.task
        except aiohttp.ClientError:
            await self.send_json("extractor_not_available")
        except RetryError:
            await self.send_json("extractor_not_available")
        else:
            success = self.task.result().resp["success"]
            if success:
                self.sessionId = self.task.result().resp["sessionId"]
                await self.send_json("subscribed_to_extractor")
        await self.connect_uri(self.congregation_group_name)

    async def disconnect_from_extractor(self):
        if self.sessionId is not None:
            count = await self.disconnect_uri(self.congregation_group_name)
            if count != 0:
                return
            try:
                self.task = asyncio.create_task(
                    self.delete_request(self.extractor_url + "api/unsubscribe/%s" % self.sessionId))
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

    @retry(retry=retry_if_exception_type(aiohttp.ClientError), stop=stop_after_attempt(7))
    async def post_request(self, url, payload):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return await response.json()

    @retry(retry=retry_if_exception_type(aiohttp.ClientError), stop=stop_after_attempt(7))
    async def delete_request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as response:
                return await response.json()

    async def connect_uri(self, group):
        host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
        redis = await aioredis.create_redis(host)
        await redis.sadd(group, self.channel_name)
        await redis.expire(group, 43200)
        redis.close()
        await redis.wait_closed()

    async def disconnect_uri(self, group):
        host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
        redis = await aioredis.create_redis(host)
        await redis.srem(group, self.channel_name)
        count = await redis.llen(group)
        redis.close()
        await redis.wait_closed()
        return count
