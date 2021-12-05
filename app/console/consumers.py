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
from asgiref.sync import sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string
from django.utils import timezone

from stage.consumers import generate_channel_group_name
from stopwatch.timer import GLOBAL_TIMERS


class TimerConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous or not user.is_authenticated:
            await self.close()
            return
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        await self.channel_layer.group_add(generate_channel_group_name("timer", congregation), self.channel_name)
        timer = GLOBAL_TIMERS.get(congregation)
        if timer is not None:
            timer.set_callback(self.timeout_callback)
        await self.accept()

    async def timer_action(self, _):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        timer = GLOBAL_TIMERS.get(congregation)
        if timer is not None:
            GLOBAL_TIMERS.get(congregation).set_callback(self.timeout_callback)

    async def timeout_callback(self, _, __, ___):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        group_name = generate_channel_group_name("console", congregation)
        await self.channel_layer.group_send(group_name, {"type": "timer.tick"})


class ConsoleConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous or not user.is_authenticated:
            await self.close()
            return
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        if "scrim" not in self.scope["session"] or self.scope["session"]["scrim"] is None:
            self.scope["session"]["scrim"] = False
        await self.channel_layer.group_add(generate_channel_group_name("console", congregation), self.channel_name)
        if self.scope["session"]["scrim"]:
            message_alert = render_to_string(template_name="stage/events/scrim.html")
        else:
            message_alert = ""
        await self.accept()
        await self.send(text_data=message_alert)
        timer = GLOBAL_TIMERS.get(congregation)
        if timer is not None:
            context = {"index": timer.get_context()["index"]}
            event = render_to_string(template_name="stopwatch/fragments/talk_index.html", context=context)
            await self.send(text_data=event)
        await self.console_scrim_refresh({})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            generate_channel_group_name("console", self.scope["url_route"]["kwargs"]["congregation"]),
            self.channel_name
        )
        raise StopConsumer()

    async def console_alert(self, event):
        await self.send(text_data=event["alert"]["value"])

    async def console_scrim(self, _):
        if not self.scope["session"]["scrim"]:
            message = render_to_string(template_name="stage/events/scrim.html")
        else:
            message = "<div id=\"overlay\"></div>"
        self.scope["session"]["scrim"] = not self.scope["session"]["scrim"]
        await sync_to_async(self.scope["session"].save)()
        await self.send(text_data=message)
        await self.console_scrim_refresh({})

    async def console_scrim_refresh(self, _):
        if not self.scope["session"]["scrim"]:
            context = {"dark": False}
        else:
            context = {"dark": True}
        message = render_to_string(template_name="console/events/scrim_control_button.html", context=context)
        await self.send(text_data=message)

    async def console_message(self, event):
        if "message" in event["message"] and event["message"]["message"] == "ACK":
            context = {"time": timezone.localtime(timezone.now())}
            text = render_to_string(template_name="console/events/ack.html", context=context)
            await self.send(text_data=text)

    async def timer_tick(self, _):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        timer = GLOBAL_TIMERS.get(congregation)
        if timer is None:
            return

        remaining_time = timer.get_formatted_remaining_time()
        elapsed_time = timer.get_formatted_elapsed_time()
        percentage = timer.get_elapsed_percentage()
        if remaining_time.startswith("-"):
            class_attr = "text-red-500 times-up"
        else:
            class_attr = ""
        event = ""
        context = {"time": elapsed_time, "full_class": class_attr}
        event = event + render_to_string(template_name="stopwatch/fragments/elapsed.html", context=context)
        context = {"time": remaining_time, "full_class": class_attr}
        event = event + render_to_string(template_name="stopwatch/fragments/remaining.html", context=context)
        context = {"percentage": percentage, "elapsed": elapsed_time, "remaining": remaining_time,
                   "full_class": class_attr}
        event = event + render_to_string(template_name="stopwatch/fragments/progress_bar.html", context=context)
        context = {"name": timer.get_timer_name()}
        event = event + render_to_string(template_name="stopwatch/fragments/talk_name_caption.html", context=context)
        await self.send(text_data=event)
