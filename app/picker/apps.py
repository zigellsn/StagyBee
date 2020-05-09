import asyncio

import aioredis
from django.apps import AppConfig
from django.conf import settings

REDIS_KEY = "stagybee::*"


async def initialize_redis():
    if "CONFIG" not in settings.CHANNEL_LAYERS["default"]:
        return
    try:
        host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
        redis = await aioredis.create_redis(host)
        for key in await redis.keys(REDIS_KEY):
            await redis.delete(key)
        redis.close()
        await redis.wait_closed()
    except OSError:
        print("Redis unavailable")


class PickerConfig(AppConfig):
    name = 'picker'
    verbose_name = "Picker"

    def ready(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize_redis())
