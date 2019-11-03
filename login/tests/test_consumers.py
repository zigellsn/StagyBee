import pytest
from channels.testing import WebsocketCommunicator

from login.consumers import ExtractorConsumer


@pytest.mark.asyncio
async def test_extractor_consumer():
    # TODO: Write tests...
    communicator = WebsocketCommunicator(ExtractorConsumer, "/ws/extractor/")
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_to(text_data="hello")
    response = await communicator.receive_from()
    assert response == "hello"
    await communicator.disconnect()
