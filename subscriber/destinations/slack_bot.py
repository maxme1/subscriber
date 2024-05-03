import logging

from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from ..models import Identifier, Post
from .interface import Destination


logger = logging.getLogger(__name__)


class SlackBot(Destination):
    app: AsyncApp
    handler: AsyncSocketModeHandler

    def __init__(self, bot_token, socket_token):
        self.app = AsyncApp(token=bot_token)
        # handlers
        self._socket_token = socket_token
        self.app.command("/subscriber")(self._link)

    async def _link(self, ack, respond, command):
        await ack()
        url = command['text'].strip()
        channel_id = command['channel_id']
        await respond(await self.subscribe(channel_id, url))

    async def notify(self, chat_id: Identifier, post: Post) -> Identifier | None:
        parts = []
        if post.title:
            parts.append({
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': post.title
                }
            })
        if post.description:
            parts.append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': post.description,
                }
            })

        parts.append({
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': post.url,
            }
        })

        response = await self.app.client.chat_postMessage(channel=chat_id, text=post.title, blocks=parts)
        return response['ts']

    async def remove(self, chat_id: Identifier, message_id: Identifier):
        await self.app.client.chat_delete(channel=chat_id, ts=message_id)

    async def start(self):
        self.handler = AsyncSocketModeHandler(self.app, self._socket_token)
        await self.handler.connect_async()

    async def stop(self):
        await self.handler.disconnect_async()
