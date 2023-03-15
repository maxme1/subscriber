from typing import Sequence

from ..crud import keep, list_chat_sources, subscribe, unsubscribe
from ..models import Identifier, Post, Source


class Destination:
    @classmethod
    def name(cls):
        return cls.__name__

    @classmethod
    async def subscribe(cls, chat_id: Identifier, url: str) -> str:
        return subscribe(chat_id, cls.name(), url)

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

    async def notify(self, chat_id: Identifier, post: Post) -> Identifier:
        pass

    async def remove(self, chat_id: Identifier, message_id: Identifier):
        pass
