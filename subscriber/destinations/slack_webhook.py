import logging

import requests

from ..models import Identifier, Post
from .interface import Destination

logger = logging.getLogger(__name__)


class SlackWebhook(Destination):
    async def notify(self, chat_id: Identifier, post: Post) -> None:
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

        req = requests.post(
            f'https://hooks.slack.com/services/{chat_id}',
            json={
                'text': post.title,
                'blocks': parts + [{
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': post.url,
                    }
                }]
            })
        if req.status_code != 200:
            logger.warning('Wrong webhook %s', req.text)

    async def remove(self, chat_id: Identifier, message_id: Identifier):
        pass

    async def start(self):
        pass

    async def stop(self):
        pass
