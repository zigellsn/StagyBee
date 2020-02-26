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

import json
from datetime import datetime

from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from audit.models import Audit
from console.models import TimeEntry
from picker.models import Credential
from stage.consumers import generate_channel_group_name
from stopwatch.timer_redis import add_timer, get_timer, remove_timer, connect_timer
from .workbook.workbook import WorkbookExtractor


class ConsoleConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.congregation = self.scope["url_route"]["kwargs"]["congregation"]
        self.language = self.scope["url_route"]["kwargs"]["language"]
        self.redis_key = f"stagybee::timer:{generate_channel_group_name('console', self.congregation)}"

    async def connect(self):
        await self.channel_layer.group_add(
            generate_channel_group_name("console", self.congregation),
            self.channel_name
        )
        await self.accept()
        await connect_timer(self, f"stagybee::timer:{generate_channel_group_name('console', self.congregation)}")
        workbook_extractor = WorkbookExtractor()
        urls = workbook_extractor.create_urls(datetime.today(), datetime.today())
        times = await workbook_extractor.get_workbooks(urls, self.language)
        if times is not None:
            dump = json.dumps(times)
            message = {"type": "times",
                       "times": dump}
            await self.send_json(message)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            generate_channel_group_name("console", self.congregation),
            self.channel_name
        )
        raise StopConsumer()

    async def receive_json(self, text_data, **kwargs):
        congregation_group_name = generate_channel_group_name("console", self.congregation)
        if "alert" in text_data:
            if text_data["alert"] == "message":
                credential = await database_sync_to_async(__get_congregation__)(self.congregation)
                await database_sync_to_async(__persist_audit_log__)(self.scope["user"].username,
                                                                    credential, text_data)
            message_type = "alert"
        elif "timer" in text_data:
            message_type = "timer"
            if text_data["timer"] == "start":
                await add_timer(self.redis_key, text_data["talk"], text_data["start"], text_data["value"])
            elif text_data["timer"] == "stop":
                credential = await database_sync_to_async(__get_congregation__)(self.congregation)
                talk, start, value = await get_timer(self.redis_key)
                json_value = json.loads(value)
                duration = int(json_value["h"]) * 3600 + int(json_value["m"]) * 60 + int(json_value["s"])
                await database_sync_to_async(__persist_time_entry__)(credential, talk, start, duration)
                await remove_timer(self.redis_key)
            else:
                return
        else:
            return
        await self.channel_layer.group_send(congregation_group_name, {"type": message_type, message_type: text_data})

    async def exit(self, event):
        await self.send_json(event)

    async def alert(self, event):
        await self.send_json(event)

    async def timer(self, event):
        await self.send_json(event)


def __get_congregation__(congregation):
    return Credential.objects.get(congregation__exact=congregation)


def __persist_time_entry__(congregation, talk, start, duration):
    start_time = datetime.strptime(start.decode("utf-8"), '%Y-%m-%dT%H:%M:%S%z')
    return TimeEntry.objects.create_time_entry(congregation, talk.decode("utf-8"), start_time, datetime.now(), duration)


def __persist_audit_log__(username, congregation, text_data):
    return Audit.objects.create_audit(congregation, username, text_data["value"])
