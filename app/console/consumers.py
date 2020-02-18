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
# from datetime import date
import json
from datetime import datetime

import aioredis
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from decouple import config
from django.conf import settings

from console.models import Audit, TimeEntry
# from get_times import extract
from picker.models import Credential
from stage.consumers import generate_channel_group_name


def get_congregation(congregation):
    return Credential.objects.get(congregation__exact=congregation)


def persist_time_entry(congregation, talk, start, duration):
    start_time = datetime.strptime(start.decode("utf-8"), '%Y-%m-%dT%H:%M:%S%z')
    return TimeEntry.objects.create_time_entry(congregation, talk, start_time, datetime.now(), duration)


class ConsoleConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.congregation = self.scope["url_route"]["kwargs"]["congregation"]
        self.redis_key = "stagybee::timer:%s" % generate_channel_group_name("console", self.congregation)

    async def connect(self):
        # times = await extract(date.today(), date.today())
        await self.channel_layer.group_add(
            generate_channel_group_name("console", self.congregation),
            self.channel_name
        )
        await self.accept()
        talk, start, value = await get_timer(self.redis_key)
        if start is not None and value is not None:
            message = {"type": "alert",
                       "alert": {"alert": "time", "talk": talk, "start": start.decode("utf-8"),
                                 "value": json.loads(value)}}
            await self.send_json(message)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            generate_channel_group_name("console", self.congregation),
            self.channel_name
        )
        raise StopConsumer()

    async def receive_json(self, text_data, **kwargs):
        congregation_group_name = generate_channel_group_name("console", self.congregation)
        if text_data["alert"] == "message":
            credential = await database_sync_to_async(get_congregation)(self.congregation)
            await database_sync_to_async(self.persist_audit_log)(credential, text_data)
        if text_data["alert"] == "time":
            await add_timer(self.redis_key, text_data["talk"], text_data["start"], text_data["value"])
        if text_data["alert"] == "stop":
            credential = await database_sync_to_async(get_congregation)(self.congregation)
            talk, start, value = await get_timer(self.redis_key)
            json_value = json.loads(value)
            duration = json_value["h"] * 3600 + json_value["m"] * 60 + json_value["s"]
            await database_sync_to_async(persist_time_entry)(credential, talk, start, duration)
            await remove_timer(self.redis_key)
        await self.channel_layer.group_send(congregation_group_name, {"type": "alert", "alert": text_data})

    async def exit(self, event):
        await self.send_json(event)

    async def alert(self, event):
        await self.send_json(event)

    def persist_audit_log(self, congregation, text_data):
        return Audit.objects.create_audit(congregation, self.scope["user"].username, text_data["value"])


class TimerConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.congregation = self.scope["url_route"]["kwargs"]["congregation"]
        self.redis_key = "stagybee::timer:%s" % generate_channel_group_name("console", self.congregation)

    async def connect(self):
        await self.channel_layer.group_add(
            generate_channel_group_name("console", self.congregation),
            self.channel_name
        )
        await self.accept()
        talk, start, value = await get_timer(self.redis_key)
        if start is not None and value is not None:
            message = {"type": "alert",
                       "alert": {"alert": "time", "talk": talk, "start": start.decode("utf-8"),
                                 "value": json.loads(value)}}
            await self.send_json(message)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            generate_channel_group_name("console", self.congregation),
            self.channel_name
        )
        raise StopConsumer()

    async def receive_json(self, text_data, **kwargs):
        congregation_group_name = generate_channel_group_name("console", self.congregation)
        await self.channel_layer.group_send(congregation_group_name, {"type": "alert", "alert": text_data})

    async def exit(self, event):
        await self.send_json(event)

    async def alert(self, event):
        await self.send_json(event)


async def add_timer(group, talk, start, value):
    redis = await connect()
    await redis.hset(group, "talk", talk)
    await redis.hset(group, "start", start)
    await redis.hset(group, "value", json.dumps(value))
    await redis.expire(group, config("REDIS_EXPIRATION", default=3600, cast=int))
    redis.close()
    await redis.wait_closed()


async def get_timer(group):
    redis = await connect()
    talk = await redis.hget(group, "talk")
    start = await redis.hget(group, "start")
    value = await redis.hget(group, "value")
    redis.close()
    await redis.wait_closed()
    return talk, start, value


async def remove_timer(group):
    redis = await connect()
    await redis.hdel(group, "talk")
    await redis.hdel(group, "start")
    await redis.hdel(group, "value")
    redis.close()
    await redis.wait_closed()


async def connect():
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
    redis = await aioredis.create_redis(host)
    return redis
