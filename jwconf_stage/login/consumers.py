import importlib
import json

import requests
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.shortcuts import get_object_or_404

picker = importlib.import_module('picker.models')


class ExtractorConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.congregation = self.scope['url_route']['kwargs']['congregation']
        self.congregation_group_name = 'congregation_%s' % self.congregation
        self.credentials = None
        self.sessionId = None
        self.extractor_url = ""

    async def connect(self):
        await self.channel_layer.group_add(
            self.congregation_group_name,
            self.channel_name
        )
        await self.accept()
        await self.connect_to_extractor()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.congregation_group_name,
            self.channel_name
        )
        await self.disconnect_from_extractor()
        raise StopConsumer()

    async def extractor_listeners(self, event):
        await self.send_json("subscribed_to_extractor")
        await self.send_json(event["listeners"])

    async def encode_json(self, content):
        if type(content) == bytes:
            new_content = json.loads(content)
            if type(new_content) == dict:
                return json.dumps(new_content)
            return new_content
        else:
            return await super().encode_json(content=content)

    async def connect_to_extractor(self):
        self.credentials = await database_sync_to_async(get_object_or_404)(picker.Credential,
                                                                           congregation=self.congregation)
        self.extractor_url = self.credentials.extractor_url
        if not self.extractor_url.endswith("/"):
            self.extractor_url = self.extractor_url + "/"
        url = "http://localhost:8000/receiver/%s/" % self.congregation
        if self.credentials.autologin is not None:
            payload = {"id": self.credentials.autologin, "url": url}
        else:
            payload = {"congregation": self.credentials.congregation,
                       "username": self.credentials.username,
                       "password": self.credentials.password,
                       "url": url}
        try:
            response = requests.post(self.extractor_url + "api/subscribe",
                                     json=payload)
        except requests.exceptions.RequestException as e:
            await self.send_json("connection_error")
        else:
            success = response.json()["success"]
            if success:
                self.sessionId = response.json()["sessionId"]
                await self.send_json("subscribed_to_extractor")
        await self.send_json("extractor_not_available")

    async def disconnect_from_extractor(self):
        if self.sessionId is not None:
            try:
                response = requests.delete(self.extractor_url + "api/unsubscribe/%s" % self.sessionId)
            except requests.exceptions.RequestException as e:
                print(e)
            else:
                success = response.json()["success"]
                if success:
                    await self.send_json("unsubscribed_from_extractor")
                    self.sessionId = None
