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
from django.utils import timezone, formats
from django.utils.translation import gettext_lazy as _

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
            await self.send(
                text_data=f"<button id=\"timer-stop\" type=\"submit\" name=\"action\" value=\"timer-stop\" "
                          f"class=\"button\" onclick=\"$('.current').next().trigger('click')\">"
                          f"<span class=\"mif-stop\"></span>{_('Stopp')}</button>")
            await self.send(
                text_data=f"<input type=\"hidden\" id=\"talk-index\" name=\"index\" value=\"{context['index']}\"/>")

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
        if event["action"] == "timer-start":
            timer = GLOBAL_TIMERS.get(congregation)
            if timer is None:
                split = str.split(event["duration"], ":")
                context = {
                    "duration": timedelta(hours=float(split[0]), minutes=float(split[1]), seconds=float(split[2])),
                    "start": timezone.now(),
                    "index": event["index"],
                    "congregation": congregation}
                GLOBAL_TIMERS[congregation] = Timer(1, self.timeout_callback, context=context,
                                                    timer_name=event["talk-name"])
                await self.send(
                    text_data=f"<input type=\"hidden\" id=\"talk-index\" name=\"index\" value=\"{context['index']}\"/>")
                await self.send(text_data=f"<div id=\"pb\" class=\"progress-bar\" style=\"width:0\">")
            await self.send(
                text_data=f"<button id=\"timer-stop\" type=\"submit\" name=\"action\" value=\"timer-stop\" "
                          f"class=\"button\" onclick=\"$('.current').next().trigger('click')\">"
                          f"<span class=\"mif-stop\"></span>{_('Stopp')}</button>")
        elif event["action"] == "timer-stop":
            timer = GLOBAL_TIMERS.get(congregation)
            if timer is not None:
                context = timer.get_context()
                credential = await database_sync_to_async(__get_congregation__)(congregation)
                await database_sync_to_async(__persist_time_entry__)(credential, timer.get_timer_name(),
                                                                     context["start"], context["duration"])
                timer.cancel()
                GLOBAL_TIMERS.pop(congregation)
            await self.send(
                text_data=f"<button id=\"timer-stop\" type=\"submit\" name=\"action\" value=\"timer-stop\" "
                          f"class=\"button disabled\"><span class=\"mif-stop\"></span>{_('Stopp')}</button>")
            await self.channel_layer.group_send(congregation_group_name,
                                                {"congregation": congregation, "activity": "stop", "type": "timer"})

    async def timer(self, event):
        if "activity" in event and event["activity"] == "stop":
            await self.send(text_data=f"<div id=\"pb\" class=\"progress-bar\" style=\"width:0\">")
            await self.send(text_data=f"<span style=\"font-family: monospace;\" id=\"stopwatch\">"
                                      f"00:00:00</span>")
            await self.send(text_data=f"<span style=\"font-family: monospace;\" id=\"remaining\">"
                                      f"00:00:00</span>")
            await self.send(text_data=f"<span id=\"talk-name-caption\"></span>")
            context = await database_sync_to_async(__get_newest__)(event["congregation"])
            if context is None:
                return
            if "-" in context.difference:
                class_attr_fg = "fg-red"
                class_attr_bg = "bg-red"
            else:
                class_attr_fg = "fg-blue"
                class_attr_bg = "bg-blue"
            await self.send(text_data="<tr id=\"no-entries\" hx-swap-oob=\"outerHTML\"></tr>")
            await self.send(text_data=f"<tbody id=\"next\" hx-swap-oob=\"beforeend\">"
                                      f"<tr>"
                                      f"<td>{context.talk}</td>"
                                      f"<td>{formats.date_format(timezone.localtime(context.start), 'TIME_FORMAT')}"
                                      f"</td>"
                                      f"<td>{formats.date_format(timezone.localtime(context.stop), 'TIME_FORMAT')}</td>"
                                      f"<td>{context.duration}</td>"
                                      f"<td>{context.display_max_duration}</td>"
                                      f"<td class=\"{class_attr_fg}\"><div>{context.difference}</div>"
                                      f"<div class=\"progress-bar {class_attr_bg}\" style=\"min-height:12px;width:"
                                      f"{str(context.percentage)}%;\"></div> "
                                      f"</td>"
                                      f"</tr>"
                                      f"</tbody>")
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
        await self.send(text_data=f"<span style=\"font-family: monospace;\" id=\"stopwatch\"{full_class}>"
                                  f"{__td_to_string__(delta)}</span>")
        await self.send(text_data=f"<span style=\"font-family: monospace;\" id=\"remaining\"{full_class}>"
                                  f"{remaining_str}</span>")
        await self.send(text_data=f"<div id=\"pb\" class=\"progress-bar\" style=\"width:{percentage}%\">")
        await self.send(text_data=f"<span id=\"talk-name-caption\">{timer.get_timer_name()}</span>")


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
