from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterable, Optional, Type

from pydantic import BaseModel

TYPE_TO_CHANNEL = {}
DOMAIN_TO_CHANNEL = {}


class Content(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    # an optional base64-encoded image
    image: Optional[str] = None


class ChannelData(BaseModel):
    # the url used to scrape for updates
    update_url: str
    # the channel name
    name: str
    # an optional base64-encoded image
    image: Optional[str] = None
    # an optional standardized channel url
    url: Optional[str] = None


class PostUpdate(BaseModel):
    id: str
    url: str
    content: Optional[Content] = None


class ChannelAdapter(ABC):
    domain: str
    queue: str = 'main'
    add_name: bool = False

    @staticmethod
    @abstractmethod
    async def track(url: str) -> ChannelData:
        """ Get essential channel information based on the provided url """

    @abstractmethod
    async def update(self, update_url: str, name: str) -> AsyncIterable[PostUpdate]:
        """ Get the list of posts for a channel """
        raise NotImplementedError
        # this line is for type checkers:
        yield  # noqa

    @abstractmethod
    async def scrape(self, post_url: str) -> Content:
        """ Get additional information for a post. Invoked only if post_update.content is None """

    @classmethod
    def name(cls):
        return cls.__name__

    @staticmethod
    def dispatch_type(type) -> Type[ChannelAdapter]:
        return TYPE_TO_CHANNEL[type]

    @staticmethod
    def dispatch_domain(domain) -> Type[ChannelAdapter]:
        return DOMAIN_TO_CHANNEL[domain]

    def __init_subclass__(cls, **kwargs):
        assert cls.__name__ not in TYPE_TO_CHANNEL
        assert cls.domain not in DOMAIN_TO_CHANNEL
        TYPE_TO_CHANNEL[cls.__name__] = cls
        DOMAIN_TO_CHANNEL[cls.domain] = cls
