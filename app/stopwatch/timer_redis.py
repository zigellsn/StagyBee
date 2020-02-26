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
from decouple import config
from django.conf import settings


async def add_timer(group, talk, start, value):
    redis = await __redis_connect()
    await redis.hset(group, "talk", talk)
    await redis.hset(group, "start", start)
    await redis.hset(group, "value", json.dumps(value))
    await redis.expire(group, config("REDIS_EXPIRATION", default=3600, cast=int))
    redis.close()
    await redis.wait_closed()


async def get_timer(group):
    redis = await __redis_connect()
    talk = await redis.hget(group, "talk")
    start = await redis.hget(group, "start")
    value = await redis.hget(group, "value")
    redis.close()
    await redis.wait_closed()
    return talk, start, value


async def remove_timer(group):
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
