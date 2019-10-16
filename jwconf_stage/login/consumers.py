from channels.generic.websocket import AsyncWebsocketConsumer


class ExtractorConsumer(AsyncWebsocketConsumer):
    groups = ["extractor"]

    async def connect(self):
        print("connect")
        await self.accept()

    async def disconnect(self, close_code):
        print("disconnect")

    async def extractor_listeners(self, event):
        if event["session"] == self.scope["session"].session_key:
            await self.send(text_data=event["message"])
