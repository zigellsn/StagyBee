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
from datetime import datetime

from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from django.conf import settings

from picker.models import Credential
from stage.consumers import generate_channel_group_name
from app.stagy_bee.consumers import AsyncJsonRedisWebsocketConsumer
from stopwatch.models import TimeEntry
from .timer import Timer, GLOBAL_TIMERS


class CentralTimerConsumer(AsyncJsonRedisWebsocketConsumer):

    async def connect(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        congregation_group_name = generate_channel_group_name("timer", congregation)
        await self.channel_layer.group_add(congregation_group_name, self.channel_name)
        await self.accept()

        timer = GLOBAL_TIMERS.get(congregation)
        if timer is not None:
            context = timer.get_context()
            start = datetime.strptime(context["start"], settings.DATETIME_FORMAT)
            delta = datetime.now() - start
            await self.channel_layer.group_send(congregation_group_name,
                                                {"timer": {"mode": "running",
                                                           "remaining": get_json_duration(delta.seconds),
                                                           "duration": context["duration"],
                                                           "name": timer.get_timer_name(),
                                                           "start": context["start"],
                                                           "index": context["index"]}, "type": "timer"})

    async def disconnect(self, close_code):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        await self.channel_layer.group_discard(generate_channel_group_name("timer", congregation), self.channel_name)
        raise StopConsumer()

    async def timeout_callback(self, name, context, _):
        congregation_group_name = generate_channel_group_name("timer",
                                                              self.scope["url_route"]["kwargs"]["congregation"])
        start = datetime.strptime(context["start"], settings.DATETIME_FORMAT)
        delta = datetime.now() - start
        await self.channel_layer.group_send(congregation_group_name,
                                            {"timer": {"mode": "sync", "remaining": get_json_duration(delta.seconds),
                                                       "duration": context["duration"],
                                                       "name": name, "index": context["index"]}, "type": "timer"})

    async def receive_json(self, text_data, **kwargs):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        congregation_group_name = generate_channel_group_name("timer", congregation)
        if "timer" not in text_data:
            return
        if text_data["timer"] == "start":
            timer = GLOBAL_TIMERS.get(congregation)
            if timer is None:
                context = {"duration": text_data["duration"],
                           "start": datetime.now().strftime(settings.DATETIME_FORMAT),
                           "index": text_data["index"]}
                GLOBAL_TIMERS[congregation] = Timer(1, self.timeout_callback, context=context,
                                                    timer_name=text_data["name"])
            await self.channel_layer.group_send(congregation_group_name,
                                                {"timer": {"mode": "started", "name": text_data["name"],
                                                           "duration": text_data["duration"],
                                                           "index": text_data["index"]}, "type": "timer"})
        elif text_data["timer"] == "stop":
            timer = GLOBAL_TIMERS.get(congregation)
            if timer is not None:
                context = timer.get_context()
                duration = get_duration(context["duration"])
                credential = await database_sync_to_async(__get_congregation__)(congregation)
                await database_sync_to_async(__persist_time_entry__)(credential, timer.get_timer_name(),
                                                                     context["start"], duration)
                timer.cancel()
                GLOBAL_TIMERS.pop(congregation)
            await self.channel_layer.group_send(congregation_group_name,
                                                {"timer": {"mode": "stopped"}, "type": "timer"})

    async def timer(self, event):
        await self.send_json(event)


def __get_congregation__(congregation):
    return Credential.objects.get(congregation__exact=congregation)


def __persist_time_entry__(congregation, talk, start, duration):
    return TimeEntry.objects.create_time_entry(congregation, talk, start, datetime.now(), duration)


def get_duration(duration):
    return int(duration["h"]) * 3600 + int(duration["m"]) * 60 + int(duration["s"])


def get_json_duration(duration):
    return {"h": int(duration / 3600), "m": int((duration % 3600) / 60), "s": (duration % 3600) % 60}
