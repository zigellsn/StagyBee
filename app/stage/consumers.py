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

import asyncio
import json
import logging
import re
from contextlib import suppress

import aiohttp
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import translation
from tenacity import retry, wait_random_exponential, stop_after_delay, retry_if_exception_type, RetryError

from StagyBee.consumers import AsyncSSEConsumer
from picker.models import Credential
from stage.timeout import GLOBAL_TIMEOUT, Timeout


def generate_channel_group_name(function, congregation):
    con = re.sub(r'[^\x2D-\x2E\x30-\x39\x41-\x5A\x5F\x61-\x7A]', '_', congregation)
    return f"congregation.{function}.{con}"


class ExtractorConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task = None
        self.extractor_url = ""
        self.show_only_request_to_speak = False
        self.sort_by_family_name = True
        self.family_name_first = True
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        await self.channel_layer.group_add(
            generate_channel_group_name("stage", congregation),
            self.channel_name
        )
        language = self.scope["url_route"]["kwargs"]["language"]
        translation.activate(language)
        await self.accept()
        context = {"connecting": True}
        await self.build_events(context)
        if congregation not in GLOBAL_TIMEOUT:
            GLOBAL_TIMEOUT[congregation] = Timeout()
        else:
            if "role" not in self.scope["url_route"]["kwargs"]:
                GLOBAL_TIMEOUT.get(congregation).count = GLOBAL_TIMEOUT.get(congregation).count + 1
        congregation_dataset = await database_sync_to_async(Credential.objects.get)(congregation=congregation)
        if congregation_dataset.sort_order == Credential.SortOrder.FAMILY_NAME:
            self.sort_by_family_name = True
        else:
            self.sort_by_family_name = False
        if congregation_dataset.name_order == Credential.NameOrder.FAMILY_NAME:
            self.family_name_first = True
        else:
            self.family_name_first = False
        await self.build_events(context)

    async def disconnect(self, close_code):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        if self.task is not None and not self.task.done():
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
        await self.channel_layer.group_discard(generate_channel_group_name("stage", congregation), self.channel_name)
        timeout = GLOBAL_TIMEOUT.get(congregation)
        if timeout is not None and "role" not in self.scope["url_route"]["kwargs"]:
            timeout.count = timeout.count - 1
            if timeout.count == 0:
                timeout.cancel()
                GLOBAL_TIMEOUT.pop(congregation)
                await self.__disconnect_from_extractor()
        raise StopConsumer()

    async def extractor_connect(self, _):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        if "session_id" in self.scope["session"] and self.scope["session"]["session_id"] is not None:
            self.logger.info(f"Extractor for {congregation} already connected.")
            return
        timeout = GLOBAL_TIMEOUT.get(congregation)
        if timeout is not None:
            timeout.cancel()
            if timeout.count <= 2 and "role" not in self.scope["url_route"]["kwargs"]:
                self.logger.info(f"Trying to connect to extractor for {congregation}...")
                await self.__connect_to_extractor()

    async def extractor_listeners(self, event):
        await self.__restart_waiter()
        new_content = json.loads(event["listeners"])["names"]
        listener_count = 0
        request_to_speak_count = 0
        if self.sort_by_family_name:
            new_content = sorted(new_content, key=lambda x: (x["familyName"].lower(), x["givenName"].lower()))
        else:
            new_content = sorted(new_content, key=lambda x: (x["givenName"].lower(), x["familyName"].lower()))
        listeners = []
        for name in new_content:
            if (self.show_only_request_to_speak and name["requestToSpeak"]) or not self.show_only_request_to_speak:
                listener_count = listener_count + name["listenerCount"]

                if name["familyName"] == "" and name["givenName"] == "":
                    continue
                if name["familyName"] == "":
                    complete_name = name["givenName"]
                elif name["givenName"] == "":
                    complete_name = name["familyName"]
                else:
                    if self.family_name_first:
                        complete_name = f"{name['familyName']}, {name['givenName']}"
                    else:
                        complete_name = f"{name['givenName']} {name['familyName']}"

                if name["requestToSpeak"] and not name["speaking"]:
                    request_to_speak_count = request_to_speak_count + 1

                listeners.append({"listener_type": name["listenerType"], "speaking": name["speaking"],
                                  "request_to_speak": name["requestToSpeak"], "complete_name": complete_name,
                                  "listener_count": name["listenerCount"]})

        context = {"listener_count": listener_count, "request_to_speak_count": request_to_speak_count,
                   "listeners": listeners}
        await self.build_events(context)

    async def build_events(self, context=None):
        event = render_to_string(template_name="stage/events/sum_listeners.html", context=context)
        await self.send(text_data=event)
        event = render_to_string(template_name="stage/events/activity.html", context=context)
        await self.send(text_data=event)
        event = render_to_string(template_name="stage/events/listeners.html", context=context)
        await self.send(text_data=event)

    async def extractor_status(self, event):
        if not json.loads(event["status"])["running"]:
            context = {"connecting": True}
            await self.build_events(context)
        else:
            context = {"listener_count": 0, "request_to_speak_count": 0}
            await self.build_events(context)

    async def __waiter(self):
        await asyncio.sleep(settings.EXTRACTOR_TIMEOUT)
        reachable = await self.__get_extractor_status()
        if not reachable:
            context = {"error": True}
            await self.build_events(context)

    async def __restart_waiter(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        timeout = GLOBAL_TIMEOUT.get(congregation)
        if timeout is not None:
            timeout.cancel()
        GLOBAL_TIMEOUT[congregation].set_timeout(self.__waiter())

    async def __get_extractor_status(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        credentials = await database_sync_to_async(get_object_or_404)(Credential, congregation=congregation)
        if credentials.touch:
            return
        self.show_only_request_to_speak = credentials.show_only_request_to_speak
        if "session_id" in self.scope["session"] and self.scope["session"]["session_id"] is not None:
            url = f"{self.extractor_url}api/status/{self.scope['session']['session_id']}"
            try:
                self.task = asyncio.create_task(
                    self.__get_request(url))
                await self.task
            except aiohttp.ClientError:
                return False
            except RetryError:
                return False
            else:
                return True

    async def __connect_to_extractor(self):
        context = {"connecting": True}
        await self.build_events(context)
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        credentials = await database_sync_to_async(get_object_or_404)(Credential, congregation=congregation)
        if credentials.touch:
            return
        self.show_only_request_to_speak = credentials.show_only_request_to_speak
        self.extractor_url = credentials.extractor_url
        if not self.extractor_url.endswith("/"):
            self.extractor_url = self.extractor_url + "/"
        receiver_host = settings.RECEIVER_HOST
        if receiver_host == "":
            receiver_host = self.scope["server"][0]
        receiver_port = settings.RECEIVER_PORT
        if receiver_port == 0:
            receiver_port = self.scope["server"][1]
        receiver_protocol = settings.RECEIVER_PROTOCOL
        url = f"{receiver_protocol}://{receiver_host}:{receiver_port}/receiver/{congregation}/"
        if credentials.autologin is not None and credentials.autologin != "":
            payload = {"id": credentials.autologin, "url": url}
        else:
            payload = {"congregation": credentials.congregation,
                       "username": credentials.username,
                       "password": credentials.password,
                       "url": url}
        try:
            self.task = asyncio.create_task(self.__post_request(self.extractor_url + "api/subscribe", payload))
            await self.task
        except aiohttp.ClientError:
            context = {"error": True}
            await self.build_events(context)
        except RetryError:
            context = {"error": True}
            await self.build_events(context)
        else:
            success = self.task.result()["success"]
            if success:
                self.scope["session"]["session_id"] = self.task.result()["sessionId"]
                timeout = GLOBAL_TIMEOUT.get(credentials.congregation)
                if timeout is not None:
                    timeout.established = True
                context = {"connecting": None, "error": None, "listener_count": 0, "request_to_speak_count": 0}
                await self.build_events(context)

    async def __disconnect_from_extractor(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        credentials = await database_sync_to_async(get_object_or_404)(Credential, congregation=congregation)
        if credentials.touch:
            return
        if "session" in self.scope and "session_id" in self.scope["session"] and \
                self.scope["session"]["session_id"] is not None:
            try:
                self.task = asyncio.create_task(
                    self.__delete_request(
                        f"{self.extractor_url}api/unsubscribe/{self.scope['session']['session_id']}"))
                await self.task
            except aiohttp.ClientError:
                context = {"error": True}
                await self.build_events(context)
            except RetryError:
                context = {"error": True}
                await self.build_events(context)
            else:
                success = self.task.result()["success"]
                if success:
                    self.scope["session"]["session_id"] = None
            await self.build_events()

    @retry(retry=retry_if_exception_type(aiohttp.ClientError), wait=wait_random_exponential(multiplier=1, max=15),
           stop=stop_after_delay(15))
    async def __post_request(self, url, payload):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, ssl=False, json=payload) as response:
                self.logger.info(f"Extractor POST {url}")
                return await response.json()

    @retry(retry=retry_if_exception_type(aiohttp.ClientError), wait=wait_random_exponential(multiplier=1, max=15),
           stop=stop_after_delay(15))
    async def __delete_request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, ssl=False) as response:
                self.logger.info(f"Extractor DELETE {url}")
                return await response.json()

    @retry(retry=retry_if_exception_type(aiohttp.ClientError), wait=wait_random_exponential(multiplier=1, max=15),
           stop=stop_after_delay(15))
    async def __get_request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False) as response:
                self.logger.info(f"Extractor GET {url}")
                return await response.json()


class MessageConsumer(AsyncSSEConsumer):

    async def handle(self, body):
        await super().add_headers()
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        await self.channel_layer.group_add(
            generate_channel_group_name("message", congregation),
            self.channel_name
        )
        language = self.scope["url_route"]["kwargs"]["language"]
        translation.activate(language)
        await self.send_body("".encode("utf-8"), more_body=True)

    async def disconnect(self):
        await self.channel_layer.group_discard(
            generate_channel_group_name("message", self.scope["url_route"]["kwargs"]["congregation"]),
            self.channel_name
        )
        raise StopConsumer()

    async def message_alert(self, event):
        message = event["alert"]["value"]
        message = message.replace("\n", "<br>")
        await self.send_body(f'event: message_alert\ndata: {message}\n\n'.encode("utf-8"),
                             more_body=True)

    async def message_cancel(self, _):
        await self.send_body(f'event: message_cancel\ndata: \n\n'.encode("utf-8"), more_body=True)
