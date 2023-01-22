#  Copyright 2019-2023 Simon Zigelli
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

import logging

from channels.exceptions import StopConsumer
from channels.generic.http import AsyncHttpConsumer
from django.template.loader import render_to_string


class AsyncSSEConsumer(AsyncHttpConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.keepalive = False

    async def add_headers(self):
        await self.send_headers(headers=[
            (b"Cache-Control", b"no-cache"),
            (b"Content-Type", b"text/event-stream"),
            (b"Transfer-Encoding", b"chunked"),
        ])

    async def send_body(self, body, *, more_body=False):
        if more_body:
            self.keepalive = True
        return await super().send_body(body, more_body=more_body)

    async def http_request(self, message):
        if "body" in message:
            self.body.append(message["body"])
        if not message.get("more_body"):
            try:
                await self.handle(b"".join(self.body))
            finally:
                if not self.keepalive:
                    await self.disconnect()
                    raise StopConsumer()

    @staticmethod
    def append_event(name, template_name=None, context=None, using=None, response=""):
        if template_name is not None:
            template = render_to_string(template_name=template_name, context=context, using=using).replace("\n", "")
        else:
            template = ""
        event = f"event: {name}\ndata: {template}\n\n"
        return f"{response}{event}"

    def handle(self, body):
        """
        Receives the request body as a bytestring. Response may be composed
        using the ``self.send*`` methods; the return value of this method is
        thrown away.
        """
        raise NotImplementedError(
            "Subclasses of AsyncHttpConsumer must provide a handle() method."
        )
