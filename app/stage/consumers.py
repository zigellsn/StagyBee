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

import asyncio
import json
import re
from contextlib import suppress

import aiohttp
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from tenacity import retry, wait_random_exponential, stop_after_delay, retry_if_exception_type, RetryError

from StagyBee.consumers import AsyncRedisWebsocketConsumer
from picker.models import Credential

GLOBAL_TIMEOUT = {}
# TODO: Translation!


def generate_channel_group_name(function, congregation):
    con = re.sub(r'[^\x2D-\x2E\x30-\x39\x41-\x5A\x5F\x61-\x7A]', '_', congregation)
    return f"congregation.{function}.{con}"


class ExtractorConsumer(AsyncRedisWebsocketConsumer):

    async def connect(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        await self.channel_layer.group_add(
            generate_channel_group_name("stage", congregation),
            self.channel_name
        )
        await self.accept()
        timeout = GLOBAL_TIMEOUT.get(congregation)
        if timeout is not None:
            timeout.cancel()
            GLOBAL_TIMEOUT.pop(congregation)
        await self.__connect_to_extractor(self.__get_redis_key(self.scope["url_route"]["kwargs"]["congregation"]))

    async def disconnect(self, close_code):
        if self.task is not None and not self.task.done():
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
        await self.channel_layer.group_discard(
            generate_channel_group_name("stage", self.scope["url_route"]["kwargs"]["congregation"]),
            self.channel_name
        )
        await self.__disconnect_from_extractor(self.__get_redis_key(self.scope["url_route"]["kwargs"]["congregation"]))
        raise StopConsumer()

    async def extractor_listeners(self, event):
        await self.__restart_waiter()
        new_content = json.loads(event["listeners"])["names"]
        listener_count = 0
        request_to_speak_count = 0
        new_content = sorted(new_content, key=lambda x: (x["familyName"].lower(), x["givenName"].lower()))
        listeners = ""
        for name in new_content:
            listener_count = listener_count + name["listenerCount"]

            if name["familyName"] == "" and name["givenName"] == "":
                continue
            if name["familyName"] == "":
                complete_name = name["givenName"]
            elif name["givenName"] == "":
                complete_name = name["familyName"]
            else:
                # TODO: Name order
                complete_name = f"{name['familyName']}, {name['givenName']}"

            if name["requestToSpeak"] and not name["speaking"]:
                speak = "bg-blue requestToSpeak"
                request_to_speak_count = request_to_speak_count + 1
            elif name["speaking"]:
                speak = "bg-green"
            else:
                speak = "bg-gray"

            if name['listenerType'] <= 3:
                listener_type = "mif-phone"
            else:
                listener_type = "mif-tablet"

            if (self.show_only_request_to_speak and name["requestToSpeak"]) or not self.show_only_request_to_speak:
                listeners = f"{listeners}<div class=\"button primary large {speak} fg-black m-1\" " \
                            f"data-size=\"wide\"><span class=\"ml-1\"><span class=\"{listener_type}\"><" \
                            f"/span>&nbsp;{complete_name}&nbsp;</span><span class=\"badge inline\">" \
                            f"{name['listenerCount']}</span></div> "

        await self.send("<div id=\"sum-listeners\"><span class=\"display1\">Zuhörer gesamt:&nbsp;</span><span "
                        f"class=\"display1\" id=\"sumListenersNumber\">{listener_count}</span><span "
                        "class=\"display1\">&nbsp;-&nbsp;</span><span "
                        "class=\"display1\">Meldungen:&nbsp;</span><span class=\"display1\" "
                        f"id=\"sumRequestToSpeakNumber\">{request_to_speak_count}</span></div>"
                        "<div id=\"activity\"></div>"
                        f"<div id=\"listeners\">{listeners}</div>")

    async def extractor_status(self, event):
        if not event["status"]["running"]:
            await self.send("<div class=\"pos-fixed pos-center\" id=\"activity\"><span id=\"ring\" class=\"pos-fixed "
                            "pos-center\" style=\"margin-top: -74px\" data-role=\"activity\" data-type=\"ring\" "
                            "data-style=\"dark\"></span><div>Verbindung zu Extraktor-Dienst wird aufgebaut...</div>"
                            "</div><div id=\"listeners\"></div><div id=\"sum-listeners\"></div>")
        else:
            await self.send("<div id=\"activity\"></div>")

    async def __waiter(self):
        await asyncio.sleep(settings.EXTRACTOR_TIMEOUT)
        reachable = await self.__get_extractor_status()
        if not reachable:
            await self.send("<div class=\"pos-fixed pos-center\" id=\"activity\"><span "
                            "class=\"mif-cancel mif-5x fg-red pos-fixed pos-center\" style=\"margin-top: "
                            "-74px\"></span>""<div>Extraktor-Dienst läuft nicht oder ist nicht erreichbar.</div></div>"
                            "<div id=\"listeners\"></div>"
                            "<div id=\"sum-listeners\"></div>")

    async def __restart_waiter(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        timeout = GLOBAL_TIMEOUT.get(congregation)
        if timeout is not None:
            timeout.cancel()
        GLOBAL_TIMEOUT[congregation] = asyncio.create_task(self.__waiter())

    @staticmethod
    def __get_redis_key(congregation):
        return f"stagybee:session:{generate_channel_group_name('stage', congregation)}"

    async def __get_extractor_status(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        credentials = await database_sync_to_async(get_object_or_404)(Credential, congregation=congregation)
        if credentials.touch:
            return
        self.show_only_request_to_speak = credentials.show_only_request_to_speak
        if "session_id" in self.scope["url_route"]["kwargs"] and \
                self.scope["url_route"]["kwargs"]["session_id"] is not None:
            url = f"{self.extractor_url}api/status/{self.scope['url_route']['kwargs']['session_id']}"
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

    async def __connect_to_extractor(self, redis_key):
        await self.send("<div class=\"pos-fixed pos-center\" id=\"activity\"><span id=\"ring\" class=\"pos-fixed "
                        "pos-center\" style=\"margin-top: -74px\" data-role=\"activity\" data-type=\"ring\" "
                        "data-style=\"dark\"></span><div>Verbindung zu Extraktor-Dienst wird aufgebaut...</div></div>"
                        "<div id=\"listeners\"></div><div id=\"sum-listeners\"></div>")
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
            await self.send("<div class=\"pos-fixed pos-center\" id=\"activity\"><span "
                            "class=\"mif-cancel mif-5x fg-red pos-fixed pos-center\" style=\"margin-top: "
                            "-74px\"></span>""<div>Extraktor-Dienst läuft nicht oder ist nicht erreichbar.</div></div>"
                            "<div id=\"listeners\"></div><div id=\"sum-listeners\"></div>")
        except RetryError:
            await self.send("<div class=\"pos-fixed pos-center\" id=\"activity\"><span "
                            "class=\"mif-cancel mif-5x fg-red pos-fixed pos-center\" style=\"margin-top: "
                            "-74px\"></span>""<div>Extraktor-Dienst läuft nicht oder ist nicht erreichbar.</div></div>"
                            "<div id=\"listeners\"></div><div id=\"sum-listeners\"></div>")
        else:
            success = self.task.result()["success"]
            if success:
                self.scope["url_route"]["kwargs"]["session_id"] = self.task.result()["sessionId"]
                await self.send("<div id=\"sum-listeners\"><span class=\"display1\">Zuhörer gesamt:&nbsp;</span><span "
                                "class=\"display1\" id=\"sumListenersNumber\"></span><span "
                                "class=\"display1\">&nbsp;-&nbsp;</span><span "
                                "class=\"display1\">Meldungen:&nbsp;</span><span class=\"display1\" "
                                "id=\"sumRequestToSpeakNumber\"></span></div>"
                                "<div id=\"activity\"></div>")
            await self._redis.connect_uri(redis_key, self.channel_name)

    async def __disconnect_from_extractor(self, redis_key):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        credentials = await database_sync_to_async(get_object_or_404)(Credential, congregation=congregation)
        if credentials.touch:
            return
        if "session_id" in self.scope["url_route"]["kwargs"] and \
                self.scope["url_route"]["kwargs"]["session_id"] is not None:
            count = await self._redis.disconnect_uri(redis_key, self.channel_name)
            self.logger.info(f"Extractor STATUS {count} listeners")
            if count != 0 and count is not None:
                return
            try:
                self.task = asyncio.create_task(
                    self.__delete_request(
                        f"{self.extractor_url}api/unsubscribe/{self.scope['url_route']['kwargs']['session_id']}"))
                await self.task
            except aiohttp.ClientError:
                await self.send("<div class=\"pos-fixed pos-center\" id=\"activity\"><span "
                                "class=\"mif-cancel mif-5x fg-red pos-fixed pos-center\" style=\"margin-top: "
                                "-74px\"></span>"
                                "<div>Extraktor-Dienst läuft nicht oder ist nicht erreichbar.</div></div>"
                                "<div id=\"listeners\"></div><div id=\"sum-listeners\"></div>")
            except RetryError:
                await self.send("<div class=\"pos-fixed pos-center\" id=\"activity\"><span "
                                "class=\"mif-cancel mif-5x fg-red pos-fixed pos-center\" style=\"margin-top: "
                                "-74px\"></span>"
                                "<div>Extraktor-Dienst läuft nicht oder ist nicht erreichbar.</div></div>"
                                "<div id=\"listeners\"></div><div id=\"sum-listeners\"></div>")
            else:
                success = self.task.result()["success"]
                if success:
                    await self.send("unsubscribed_from_extractor")
                    self.scope["url_route"]["kwargs"]["session_id"] = None

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


class ConsoleClientConsumer(AsyncRedisWebsocketConsumer):

    async def connect(self):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        await self.channel_layer.group_add(
            generate_channel_group_name("console", congregation),
            self.channel_name
        )
        await self.accept()
        await self._redis.connect_uri(self.__get_redis_key(congregation), self.channel_name)

    async def disconnect(self, close_code):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        congregation_channel_group = generate_channel_group_name("console", congregation)
        count = await self._redis.disconnect_uri(self.__get_redis_key(congregation), self.channel_name)
        self.logger.info(f"Extractor STATUS {count} listeners")
        if count == 0:
            await self.channel_layer.group_send(congregation_channel_group, {"type": "exit"})
        await self.channel_layer.group_discard(congregation_channel_group, self.channel_name)
        raise StopConsumer()

    async def websocket_receive(self, text_data):
        congregation = self.scope["url_route"]["kwargs"]["congregation"]
        congregation_channel_group = generate_channel_group_name("console", congregation)
        if "text" in text_data and "message" in text_data["text"]:
            await self.channel_layer.group_send(congregation_channel_group,
                                                {"type": "message", "message": text_data["text"]})

    async def alert(self, event):
        if "alert" in event:
            message_alert = "<div id=\"alert\"><span class=\"button square closer\"></span><div " \
                            f"class=\"info-box-content\"><h3>{_('Nachricht')}</h3><p>{event['alert']['value']}" \
                            "</p></div></div>"
            await self.send(text_data=message_alert)

    async def scrim(self, event):
        if "scrim" in event:
            if event["scrim"]["value"]:
                message_alert = "<div id=\"scrim\"><div id=\"overlay\" style=\"display: block;\"></div></div>"
            else:
                message_alert = "<div id=\"scrim\"></div>"
            await self.send(text_data=message_alert)

    async def timer(self, event):
        pass

    async def message(self, event):
        pass

    async def status(self, event):
        pass

    @staticmethod
    def __get_redis_key(congregation):
        return f"stagybee:console:{generate_channel_group_name('console', congregation)}"
