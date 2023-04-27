import logging
from typing import Sequence
from urllib.parse import urlparse

from ..crud import keep, list_chat_sources, subscribe, unsubscribe
from ..models import Identifier, Post, Source
from ..sources import ChannelAdapter

logger = logging.getLogger(__name__)


class Destination:
    @classmethod
    def name(cls):
        return cls.__name__

    @classmethod
    async def subscribe(cls, chat_id: Identifier, url: str) -> str:
        parts = urlparse(url)
        domain = '.'.join(parts.netloc.split('.')[-2:]).lower()

        try:
            adapter = ChannelAdapter.dispatch_domain(domain)
        except KeyError:
            return f'Unknown domain: {domain}'

        try:
            data = await adapter.track(url)
            if data.url is not None:
                url = data.url

            subscribe(chat_id, cls.name(), adapter.name(), url, data)
            return 'Done'

        except Exception:
            logger.exception('Exception while subscribing')
            return 'An unknown error occurred'

    @staticmethod
    async def unsubscribe(chat_id: Identifier, source_id: Identifier):
        unsubscribe(chat_id, int(source_id))

    @classmethod
    async def list(cls, chat_id: Identifier) -> Sequence[Source]:
        return list_chat_sources(chat_id, cls.name())

    @staticmethod
    async def keep(message_id: Identifier):
        keep(message_id)

    async def save_image(self, hash_: str, identifier: str):
        pass

    # abstract

    async def start(self):
        pass

    async def stop(self):
        pass

    async def notify(self, chat_id: Identifier, post: Post) -> Identifier | None:
        pass

    async def remove(self, chat_id: Identifier, message_id: Identifier):
        pass
