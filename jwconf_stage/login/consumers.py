from channels.generic.websocket import AsyncWebsocketConsumer


class ExtractorConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.congregation = self.scope['url_route']['kwargs']['congregation']
        self.congregation_group_name = 'congregation_%s' % self.congregation

    async def connect(self):
        print("connect")
        await self.channel_layer.group_add(
            self.congregation_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        print("disconnect")
        await self.channel_layer.group_discard(
            self.congregation_group_name,
            self.channel_name
        )

    async def extractor_listeners(self, event):
        await self.send(text_data=event["message"])
