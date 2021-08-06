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

from datetime import datetime

from channels.exceptions import StopConsumer
from django.utils import formats, translation
from django.utils.translation import gettext_lazy as _

from StagyBee.consumers import AsyncRedisHttpConsumer
from audit.models import Audit
from picker.models import Credential
from stage.consumers import generate_channel_group_name


class ConsoleConsumer(AsyncRedisHttpConsumer):

    async def handle(self, body):
        await self.send_headers(headers=[
            (b"Cache-Control", b"no-cache"),
            (b"Content-Type", b"text/event-stream"),
            (b"Transfer-Encoding", b"chunked"),
        ])
        user = self.scope['user']
        if user.is_anonymous or not user.is_authenticated:
            raise StopConsumer()
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        await self.channel_layer.group_add(
            generate_channel_group_name("console", congregation),
            self.channel_name
        )
        await self.send_body("".encode("utf-8"), more_body=True)

    async def disconnect(self):
        await self.channel_layer.group_discard(
            generate_channel_group_name("console", self.scope["url_route"]["kwargs"]["congregation"]),
            self.channel_name
        )

    async def alert(self, event):
        pass

    async def scrim(self, event):
        pass

    async def status(self, event):
        pass

    async def timer(self, event):
        pass

    async def exit(self, event):
        pass

    async def message(self, event):
        text = ""
        if event["message"]["message"] == "ACK":
            time = datetime.now()
            old_lang = translation.get_language()
            translation.activate(self.scope["url_route"]["kwargs"]["language"])
            time = formats.date_format(time, "DATETIME_FORMAT")
            translation.activate(old_lang)
            text = f"event: message\ndata: {_('Nachricht vom %s bestätigt.') % time}\n\n"
        await self.send_body(text.encode("utf-8"), more_body=True)

    @staticmethod
    def __get_redis_key(congregation):
        return f"stagybee::timer:{generate_channel_group_name('console', congregation)}"


def __get_congregation__(congregation):
    return Credential.objects.get(congregation__exact=congregation)


def __persist_audit_log__(user, congregation, text_data):
    return Audit.objects.create_audit(congregation, user, text_data["value"])
