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

from datetime import datetime

import aioredis
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings


class RedisConnector(object):

    def __init__(self):
        self._host = None
        if "CONFIG" in settings.CHANNEL_LAYERS["default"]:
            self._host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]

    async def redis_connect(self):
        if self._host is not None:
            return await aioredis.create_redis(self._host)

    @staticmethod
    async def redis_disconnect(redis):
        redis.close()
        await redis.wait_closed()

    async def connect_uri(self, group, channel_name):
        redis = await self.redis_connect()
        if redis is None:
            return
        await redis.sadd(group, channel_name)
        members = await redis.smembers(group)
        with_since = [x for x in members if x.decode("utf-8").startswith("since:")]
        if not with_since:
            date = f"since:{datetime.now()}"
            await redis.sadd(group, date)
        await redis.expire(group, settings.REDIS_EXPIRATION)
        await self.redis_disconnect(redis)

    async def disconnect_uri(self, group, channel_name):
        redis = await self.redis_connect()
        if redis is None:
            return
        await redis.srem(group, channel_name)
        count = await redis.scard(group)
        if count == 1:
            members = await redis.smembers(group)
            await redis.srem(group, members[0])
            count = count - 1
        await self.redis_disconnect(redis)
        return count


class AsyncJsonRedisWebsocketConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._redis = RedisConnector()

    def set_redis(self, redis):
        self._redis = redis
