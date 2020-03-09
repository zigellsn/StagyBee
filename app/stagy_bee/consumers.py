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
import json

import aioredis
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from decouple import config
from django.conf import settings
from datetime import datetime


class RedisConnector(object):

    def __init__(self):
        self._host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]

    async def redis_connect(self):
        return await aioredis.create_redis(self._host)

    @staticmethod
    async def redis_disconnect(redis):
        redis.close()
        await redis.wait_closed()

    async def connect_uri(self, group, channel_name):
        redis = await self.redis_connect()
        await redis.sadd(group, channel_name)
        members = await redis.smembers(group)
        with_since = [x for x in members if x.decode("utf-8").startswith("since:")]
        if not with_since:
            date = f"since:{datetime.now()}"
            await redis.sadd(group, date)
        await redis.expire(group, config("REDIS_EXPIRATION", default=21600, cast=int))
        await self.redis_disconnect(redis)

    async def disconnect_uri(self, group, channel_name):
        redis = await self.redis_connect()
        await redis.srem(group, channel_name)
        count = await redis.scard(group)
        if count == 1:
            members = await redis.smembers(group)
            await redis.srem(group, members[0])
            count = count - 1
        await self.redis_disconnect(redis)
        return count

    async def connect_timer(self, redis_key):
        talk, start, value, index = await self.get_timer(redis_key)
        if start is not None and value is not None:
            message = {"type": "timer",
                       "timer": {"timer": "start", "talk": talk.decode("utf-8"), "start": start.decode("utf-8"),
                                 "value": json.loads(value), "index": index}}
            return message

    async def add_timer(self, group, talk, start, value, index):
        redis = await self.redis_connect()
        await redis.hset(group, "talk", talk)
        await redis.hset(group, "start", start)
        await redis.hset(group, "value", json.dumps(value))
        await redis.hset(group, "index", index)
        await redis.expire(group, config("REDIS_EXPIRATION", default=3600, cast=int))
        await self.redis_disconnect(redis)

    async def get_timer(self, group):
        redis = await self.redis_connect()
        talk = await redis.hget(group, "talk")
        start = await redis.hget(group, "start")
        value = await redis.hget(group, "value")
        index = await redis.hget(group, "index")
        if index is None:
            index = -1
        await self.redis_disconnect(redis)
        return talk, start, value, int(index)

    async def remove_timer(self, group):
        redis = await self.redis_connect()
        await redis.hdel(group, "talk")
        await redis.hdel(group, "start")
        await redis.hdel(group, "value")
        await self.redis_disconnect(redis)


class AsyncJsonRedisWebsocketConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._redis = RedisConnector()

    def set_redis(self, redis):
        self._redis = redis
