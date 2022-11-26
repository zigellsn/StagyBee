#  Copyright 2019-2022 Simon Zigelli
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
import logging

import redis
import redis.asyncio as aioredis
from django.apps import AppConfig
from django.conf import settings

REDIS_KEY = "stagybee:*"


async def initialize_redis():
    await __initialize_redis("default")


async def __initialize_redis(layer):
    if "CONFIG" not in settings.CHANNEL_LAYERS[layer]:
        return
    try:
        host = settings.CHANNEL_LAYERS[layer]["CONFIG"]["hosts"][0]
        pool = aioredis.ConnectionPool.from_url(host)
        connection = aioredis.Redis(connection_pool=pool)
        for key in await connection.keys(REDIS_KEY):
            await connection.delete(key)
        await connection.close(close_connection_pool=True)
    except redis.exceptions.ConnectionError:
        log = logging.getLogger(__name__)
        log.warning("Redis unavailable")


class PickerConfig(AppConfig):
    name = "picker"
    verbose_name = "JWConf Picker"

    def ready(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(initialize_redis())
        if not loop.is_closed():
            loop.close()
        pass
