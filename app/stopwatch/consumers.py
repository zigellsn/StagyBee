#  Copyright 2019-2021 Simon Zigelli
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
from datetime import timedelta

from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from django.template.loader import render_to_string
from django.utils import timezone

from StagyBee.consumers import AsyncRedisWebsocketConsumer
from picker.models import Credential
from stage.consumers import generate_channel_group_name
from stopwatch.models import TimeEntry
from .timer import Timer, GLOBAL_TIMERS


class CentralTimerConsumer(AsyncRedisWebsocketConsumer):

    async def connect(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        congregation_group_name = generate_channel_group_name("timer", congregation)
        await self.channel_layer.group_add(congregation_group_name, self.channel_name)
        await self.accept()

        timer = GLOBAL_TIMERS.get(congregation)
        if timer is not None:
            context = timer.get_context()
            timer.set_callback(self.timeout_callback)
            stop = render_to_string(template_name="stopwatch/fragments/stop.html", context={"disabled": False})
            await self.send(text_data=stop)
            talk_index = render_to_string(template_name="stopwatch/fragments/talk_index.html", context=context)
            await self.send(text_data=talk_index)

    async def disconnect(self, close_code):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        await self.channel_layer.group_discard(generate_channel_group_name("timer", congregation), self.channel_name)
        raise StopConsumer()

    async def timeout_callback(self, name, context, _):
        congregation_group_name = generate_channel_group_name("timer", context["congregation"])
        await self.channel_layer.group_send(congregation_group_name,
                                            {"congregation": context["congregation"], "type": "timer"})

    async def receive(self, text_data=None, bytes_data=None):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        congregation_group_name = generate_channel_group_name("timer", congregation)
        event = json.loads(text_data)
        if "action" not in event and (event["action"] != "start" or event["action"] != "stop"):
            return
        if event["h"] == "0" and event["m"] == "0" and event["s"] == "0":
            return
        if event["action"] == "timer-start":
            timer = GLOBAL_TIMERS.get(congregation)
            if timer is None:
                context = {
                    "duration": timedelta(hours=float(event["h"]), minutes=float(event["m"]),
                                          seconds=float(event["s"])),
                    "start": timezone.now(),
                    "index": event["index"],
                    "congregation": congregation}
                GLOBAL_TIMERS[congregation] = Timer(1, self.timeout_callback, context=context,
                                                    timer_name=event["talk-name"])
                talk_index = render_to_string(template_name="stopwatch/fragments/talk_index.html", context=context)
                await self.send(text_data=talk_index)
                progress_bar = render_to_string(template_name="stopwatch/fragments/progress_bar.html",
                                                context={"percentage": 0})
                await self.send(text_data=progress_bar)
            stop = render_to_string(template_name="stopwatch/fragments/stop.html", context={"disabled": False})
            await self.send(text_data=stop)
        elif event["action"] == "timer-stop":
            timer = GLOBAL_TIMERS.get(congregation)
            if timer is not None:
                context = timer.get_context()
                credential = await database_sync_to_async(__get_congregation__)(congregation)
                await database_sync_to_async(__persist_time_entry__)(credential, timer.get_timer_name(),
                                                                     context["start"], context["duration"])
                timer.cancel()
                GLOBAL_TIMERS.pop(congregation)
            stop = render_to_string(template_name="stopwatch/fragments/stop.html", context={"disabled": True})
            await self.send(text_data=stop)
            await self.channel_layer.group_send(congregation_group_name,
                                                {"congregation": congregation, "activity": "stop", "type": "timer"})

    async def timer(self, event):
        if "activity" in event and event["activity"] == "stop":
            progress_bar = render_to_string(template_name="stopwatch/fragments/progress_bar.html",
                                            context={"percentage": 0})
            await self.send(text_data=progress_bar)
            stopwatch = render_to_string(template_name="stopwatch/fragments/stopwatch.html",
                                         context={"time": "00:00:00"})
            await self.send(text_data=stopwatch)
            remaining = render_to_string(template_name="stopwatch/fragments/remaining.html",
                                         context={"time": "00:00:00"})
            await self.send(text_data=remaining)
            talk_name = render_to_string(template_name="stopwatch/fragments/talk_name_caption.html",
                                         context={"name": ""})
            await self.send(text_data=talk_name)
            context = await database_sync_to_async(__get_newest__)(event["congregation"])
            if context is None:
                return
            no_entries = render_to_string(template_name="stopwatch/fragments/no_entries.html")
            await self.send(text_data=no_entries)
            list_item = render_to_string(template_name="stopwatch/fragments/timeentry_list_item.html",
                                         context={"object": context})
            await self.send(text_data=list_item)
            return
        timer = GLOBAL_TIMERS.get(event["congregation"])
        if timer is None:
            return
        context = timer.get_context()
        delta = timezone.localtime(timezone.now()) - context["start"]
        remaining = context["duration"] - delta
        percentage = (delta / context["duration"]) * 100
        if remaining > timedelta():
            remaining_str = __td_to_string__(remaining)
            class_attr = ""
        else:
            remaining_str = f"-{__td_to_string__(abs(remaining))}"
            class_attr = "fg-red times-up"
        full_class = ""
        if class_attr != "":
            full_class = f" class=\"{class_attr}\""
        stopwatch = render_to_string(template_name="stopwatch/fragments/stopwatch.html",
                                     context={"time": __td_to_string__(delta), "full_class": full_class})
        await self.send(text_data=stopwatch)
        remaining = render_to_string(template_name="stopwatch/fragments/remaining.html",
                                     context={"time": remaining_str, "full_class": full_class})
        await self.send(text_data=remaining)
        progress_bar = render_to_string(template_name="stopwatch/fragments/progress_bar.html",
                                        context={"percentage": percentage})
        await self.send(text_data=progress_bar)
        talk_name = render_to_string(template_name="stopwatch/fragments/talk_name_caption.html",
                                     context={"name": timer.get_timer_name()})
        await self.send(text_data=talk_name)


def __get_congregation__(congregation):
    return Credential.objects.get(congregation__exact=congregation)


def __get_newest__(congregation):
    return TimeEntry.objects.newest(congregation)


def __persist_time_entry__(congregation, talk, start, duration):
    return TimeEntry.objects.create_time_entry(congregation, talk, start, timezone.now(), duration.total_seconds())


def __td_to_string__(delta) -> str:
    mm, ss = divmod(delta.seconds, 60)
    hh, mm = divmod(mm, 60)
    s = "%02d:%02d:%02d" % (hh, mm, ss)
    if delta.days:
        def plural(n):
            return n, abs(n) != 1 and "s" or ""

        s = ("%d day%s, " % plural(delta.days)) + s
    return s
