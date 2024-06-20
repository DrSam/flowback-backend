from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from flowback.chat.consumers import ChatConsumer
from channels.testing import WebsocketCommunicator
from urllib.parse import urlencode
from channels.security.websocket import AllowedHostsOriginValidator
from backend.middleware import TokenAuthMiddleware
from django.test import TransactionTestCase
from channels.db import database_sync_to_async
from rest_framework.authtoken.models import Token
from django.test import TransactionTestCase
from asgiref.sync import sync_to_async

from ..services import (
    message_channel_join,
)

from .factories import (
    MessageChannelFactory,
    MessageChannelParticipantFactory,
    MessageChannelTopicFactory,
    MessageFileCollectionFactory,
)
from ...user.tests.factories import UserFactory

@database_sync_to_async
def get_or_create_token(user):
    return Token.objects.get_or_create(user=user)

class ChatWSTest(TransactionTestCase):
    def setUp(self):
        self.user_one = UserFactory()
        self.user_two = UserFactory()
        self.message_channel = MessageChannelFactory()
        self.message_channel_participant_one = MessageChannelParticipantFactory(
            channel=self.message_channel
        )
        self.message_channel_participant_two = MessageChannelParticipantFactory(
            channel=self.message_channel
        )
        self.message_channel_topic = MessageChannelTopicFactory(
            channel=self.message_channel
        )
        self.message_channel_file_collection = MessageFileCollectionFactory(
            channel=self.message_channel
        )

    async def test_chat_ws(self):
        # Define the application with AuthMiddlewareStack
        application = ProtocolTypeRouter(
            {
                "websocket": AllowedHostsOriginValidator(
                    TokenAuthMiddleware(
                        URLRouter(
                            [
                                path("chat/ws/", ChatConsumer.as_asgi()),
                            ]
                        )
                    )
                ),
            }
        )

        participant = await sync_to_async(message_channel_join)(
            user_id=self.user_one.id, channel_id=self.message_channel.id
        )

        token, created = await get_or_create_token(self.user_one)

        # Encode the token in the query string
        query_string = urlencode({"token": token.key})
        test_path = f"/chat/ws/?{query_string}"

        communicator = WebsocketCommunicator(application, test_path)
        connected, subprotocol = await communicator.connect()
        assert connected  # This should be True if everything is configured correctly

        await communicator.send_json_to(
            {"channel_id": f"{self.message_channel.id}", "method": "connect_channel"}
        )

        await communicator.send_json_to(
            {
                "channel_id": f"{self.message_channel.id}",
                "message": "test",
                "method": "message_create",
                "topic_id": "93",
            }
        )
        # Don't forget to disconnect after the test
        await communicator.disconnect()
