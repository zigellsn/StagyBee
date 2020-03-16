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
from django.utils import formats, translation

from audit.models import Audit
from picker.models import Credential
from stage.consumers import generate_channel_group_name
from stagy_bee.consumers import AsyncJsonRedisWebsocketConsumer
from .workbook.workbook import WorkbookExtractor


class ConsoleConsumer(AsyncJsonRedisWebsocketConsumer):

    async def connect(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        await self.channel_layer.group_add(
            generate_channel_group_name("console", congregation),
            self.channel_name
        )
        await self.accept()
        workbook_extractor = WorkbookExtractor()
        urls = workbook_extractor.create_urls(datetime.today(), datetime.today())
        times = await workbook_extractor.get_workbooks(urls, self.scope["url_route"]["kwargs"]["language"])
        if times is not None:
            dump = json.dumps(times)
            message = {"type": "times",
                       "times": dump}
            await self.send_json(message)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            generate_channel_group_name("console", self.scope["url_route"]["kwargs"]["congregation"]),
            self.channel_name
        )
        raise StopConsumer()

    async def receive_json(self, text_data, **kwargs):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        congregation_group_name = generate_channel_group_name("console", congregation)
        if "alert" in text_data:
            if text_data["alert"] == "message":
                credential = await database_sync_to_async(__get_congregation__)(congregation)
                await database_sync_to_async(__persist_audit_log__)(self.scope["user"].username,
                                                                    credential, text_data)
            message_type = "alert"
        else:
            return
        await self.channel_layer.group_send(congregation_group_name, {"type": message_type, message_type: text_data})

    async def exit(self, event):
        await self.send_json(event)

    async def alert(self, event):
        await self.send_json(event)

    async def timer(self, event):
        await self.send_json(event)

    async def message(self, event):
        if event["message"]["message"] == "ACK":
            time = datetime.fromtimestamp(event["message"]["time"] / 1000)
            old_lang = translation.get_language()
            translation.activate(self.scope["url_route"]["kwargs"]["language"])
            event["message"]["time"] = formats.date_format(time, "DATETIME_FORMAT")
            translation.activate(old_lang)
        await self.send_json(event)

    @staticmethod
    def __get_redis_key(congregation):
        return f"stagybee::timer:{generate_channel_group_name('console', congregation)}"


def __get_congregation__(congregation):
    return Credential.objects.get(congregation__exact=congregation)


def __persist_audit_log__(username, congregation, text_data):
    return Audit.objects.create_audit(congregation, username, text_data["value"])
