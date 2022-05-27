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
import math

from asgiref.sync import sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string
from django.utils import timezone, translation

from StagyBee.settings import COLOR_GRADIENT
from stage.consumers import generate_channel_group_name
from stopwatch.timer import GLOBAL_TIMERS


class TimerConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous or not user.is_authenticated:
            await self.close()
            return
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        language = self.scope["url_route"]["kwargs"]["language"]
        translation.activate(language)
        await self.channel_layer.group_add(generate_channel_group_name("timer", congregation), self.channel_name)
        timer = GLOBAL_TIMERS.get(congregation)
        if timer is not None:
            timer.set_callback(self.timer_callback)
        await self.accept()

    async def timer_action(self, _):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        timer = GLOBAL_TIMERS.get(congregation)
        if timer is not None:
            GLOBAL_TIMERS.get(congregation).set_callback(self.timer_callback)

    async def timer_callback(self, timer, running):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        group_name = generate_channel_group_name("console", congregation)
        if running:
            await self.channel_layer.group_send(group_name, {"type": "timer.tick"})
        else:
            remaining_time = timer.get_formatted_remaining_time()
            elapsed_time = timer.get_formatted_elapsed_time()
            percentage = timer.get_elapsed_percentage()
            await self.channel_layer.group_send(group_name, {"type": "timer.stop", "data": {"remaining": remaining_time,
                                                                                            "elapsed": elapsed_time,
                                                                                            "percentage": percentage}})


class ConsoleConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # user = self.scope["user"]
        # if user.is_anonymous or not user.is_authenticated:
        #     await self.close()
        #     return
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        language = self.scope["url_route"]["kwargs"]["language"]
        translation.activate(language)
        if "session" in self.scope:
            if "scrim" not in self.scope["session"] or self.scope["session"]["scrim"] is None:
                self.scope["session"]["scrim"] = False
            await self.channel_layer.group_add(generate_channel_group_name("console", congregation), self.channel_name)
            if self.scope["session"]["scrim"]:
                message_alert = render_to_string(template_name="stage/events/scrim.html")
            else:
                message_alert = ""
            wait_for_ack = False
            if "message_wait_for_ack" not in self.scope["session"] or \
                    self.scope["session"]["message_wait_for_ack"] is None:
                self.scope["session"]["message_wait_for_ack"] = False
            else:
                if self.scope["session"]["message_wait_for_ack"]:
                    wait_for_ack = True
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
        if wait_for_ack:
            await self.console_wait_for_ack({})

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
            message = '<div id="overlay"></div>'
        self.scope["session"]["scrim"] = not self.scope["session"]["scrim"]
        await sync_to_async(self.scope["session"].save)()
        await self.send(text_data=message)
        await self.console_scrim_refresh({})

    async def console_scrim_refresh(self, _):
        if "session" in self.scope:
            if not self.scope["session"]["scrim"]:
                context = {"dark": False}
            else:
                context = {"dark": True}
        else:
            context = {"dark": False}
        message = render_to_string(template_name="console/fragments/scrim_control_button.html", context=context)
        await self.send(text_data=message)

    async def console_message(self, event):
        if "message" in event["message"] and event["message"]["message"] == "ACK":
            if "session" in self.scope:
                self.scope["session"]["message_wait_for_ack"] = False
                await sync_to_async(self.scope["session"].save)()
            context = {"time": timezone.localtime(timezone.now())}
            text = render_to_string(template_name="console/events/ack.html", context=context)
            await self.send(text_data=text)
            text = '<div id="waiting-indicator"></div>'
            await self.send(text_data=text)

    async def console_wait_for_ack(self, _):
        if "session" in self.scope:
            self.scope["session"]["message_wait_for_ack"] = True
            await sync_to_async(self.scope["session"].save)()
        text = render_to_string(template_name="console/events/waiting.html")
        await self.send(text_data=text)

    async def console_cancel_message(self, _):
        if "session" in self.scope:
            self.scope["session"]["message_wait_for_ack"] = False
            await sync_to_async(self.scope["session"].save)()
        text = '<div id="waiting-indicator"></div>'
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
        await self.build_events(class_attr, elapsed_time, percentage, remaining_time)
        context = {"name": timer.get_timer_name()}
        event = render_to_string(template_name="stopwatch/fragments/talk_name_caption.html", context=context)
        await self.send(text_data=event)

    async def timer_stop(self, event):
        if "data" not in event:
            return
        remaining_time = event["data"]["remaining"]
        elapsed_time = event["data"]["elapsed"]
        percentage = event["data"]["percentage"]
        if remaining_time.startswith("-"):
            class_attr = "animate-pulse text-red-500 times-up"
        else:
            class_attr = "animate-pulse"
        await self.build_events(class_attr, elapsed_time, percentage, remaining_time)
        event = '<div id="stop"></div>'
        await self.send(text_data=event)

    async def build_events(self, class_attr, elapsed_time, percentage, remaining_time):
        index = int(math.floor(percentage))
        if index > 99:
            index = 99
        color = COLOR_GRADIENT["hex"][index]

        context = {"time": elapsed_time, "full_class": class_attr}
        event = render_to_string(template_name="stopwatch/fragments/elapsed.html", context=context)
        await self.send(text_data=event)
        context = {"time": remaining_time, "full_class": class_attr}
        event = render_to_string(template_name="stopwatch/fragments/remaining.html", context=context)
        await self.send(text_data=event)
        context = {"percentage": percentage, "elapsed": elapsed_time, "remaining": remaining_time, "color": color,
                   "full_class": class_attr}
        event = render_to_string(template_name="stopwatch/fragments/progress_bar.html", context=context)
        await self.send(text_data=event)
        return event
