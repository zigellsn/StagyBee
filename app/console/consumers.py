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


class ConsoleConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.congregation = self.scope["url_route"]["kwargs"]["congregation"]
        self.redis_key = f"stagybee::timer:{generate_channel_group_name('console', self.congregation)}"

    async def connect(self):
        # times = await extract(date.today(), date.today())
        await __connect__(self)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            generate_channel_group_name("console", self.congregation),
            self.channel_name
        )
        raise StopConsumer()

    async def receive_json(self, text_data, **kwargs):
        congregation_group_name = generate_channel_group_name("console", self.congregation)
        if "alert" in text_data and text_data["alert"] == "message":
            credential = await database_sync_to_async(__get_congregation__)(self.congregation)
            await database_sync_to_async(__persist_audit_log__)(self.scope["user"].username,
                                                                credential, text_data)
            message_type = "alert"
        elif "timer" in text_data:
            message_type = "timer"
            if text_data["timer"] == "start":
                await __add_timer__(self.redis_key, text_data["talk"], text_data["start"], text_data["value"])
            elif text_data["timer"] == "stop":
                credential = await database_sync_to_async(__get_congregation__)(self.congregation)
                talk, start, value = await __get_timer__(self.redis_key)
                json_value = json.loads(value)
                duration = json_value["h"] * 3600 + json_value["m"] * 60 + json_value["s"]
                await database_sync_to_async(__persist_time_entry__)(credential, talk, start, duration)
                await __remove_timer__(self.redis_key)
            else:
                return
        else:
            return
        await self.channel_layer.group_send(congregation_group_name, {"type": message_type, message_type: text_data})

    async def exit(self, event):
        await self.send_json(event)

    async def alert(self, event):
        await self.send_json(event)

    async def timer(self, event):
        await self.send_json(event)


class TimerConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.congregation = self.scope["url_route"]["kwargs"]["congregation"]
        self.redis_key = f"stagybee::timer:{generate_channel_group_name('console', self.congregation)}"

    async def connect(self):
        await __connect__(self)

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


async def __add_timer__(group, talk, start, value):
    redis = await __redis_connect()
    await redis.hset(group, "talk", talk)
    await redis.hset(group, "start", start)
    await redis.hset(group, "value", json.dumps(value))
    await redis.expire(group, config("REDIS_EXPIRATION", default=3600, cast=int))
    redis.close()
    await redis.wait_closed()


async def __get_timer__(group):
    redis = await __redis_connect()
    talk = await redis.hget(group, "talk")
    start = await redis.hget(group, "start")
    value = await redis.hget(group, "value")
    redis.close()
    await redis.wait_closed()
    return talk, start, value


async def __remove_timer__(group):
    redis = await __redis_connect()
    await redis.hdel(group, "talk")
    await redis.hdel(group, "start")
    await redis.hdel(group, "value")
    redis.close()
    await redis.wait_closed()


async def __redis_connect():
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
    redis = await aioredis.create_redis(host)
    return redis


def __get_congregation__(congregation):
    return Credential.objects.get(congregation__exact=congregation)


def __persist_time_entry__(congregation, talk, start, duration):
    start_time = datetime.strptime(start.decode("utf-8"), '%Y-%m-%dT%H:%M:%S%z')
    return TimeEntry.objects.create_time_entry(congregation, talk, start_time, datetime.now(), duration)


def __persist_audit_log__(username, congregation, text_data):
    return Audit.objects.create_audit(congregation, username, text_data["value"])


async def __connect__(self):
    await self.channel_layer.group_add(
        generate_channel_group_name("console", self.congregation),
        self.channel_name
    )
    await self.accept()
    talk, start, value = await __get_timer__(self.redis_key)
    if start is not None and value is not None:
        message = {"type": "timer",
                   "timer": {"timer": "start", "talk": int(talk), "start": start.decode("utf-8"),
                             "value": json.loads(value)}}
        await self.send_json(message)
