from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterable, Optional, Type
from urllib.parse import urlparse

from aiohttp import ClientSession
from pydantic import BaseModel


TYPE_TO_CHANNEL: dict[str, Type[ChannelAdapter]] = {}
DOMAIN_TO_CHANNEL = {}


class VisibleError(Exception):
    def __init__(self, message: str):
        self.message = message


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
    queue: str = 'main'
    add_name: bool = False

    @classmethod
    @abstractmethod
    def match(cls, url: str) -> bool:
        """ Check if the provided url can be handled by the adapter """

    @staticmethod
    @abstractmethod
    async def track(url: str) -> ChannelData:
        """ Get essential channel information based on the provided url """

    @abstractmethod
    async def update(self, update_url: str, name: str, session: ClientSession) -> AsyncIterable[PostUpdate]:
        """ Get the list of posts for a channel """
        raise NotImplementedError
        # this line is for type checkers:
        yield  # noqa

    @abstractmethod
    async def scrape(self, post_url: str, session: ClientSession) -> Content:
        """ Get additional information for a post. Invoked only if post_update.content is None """

    @classmethod
    def name(cls):
        return cls.__name__

    @staticmethod
    def dispatch_type(type: str) -> Type[ChannelAdapter]:
        return TYPE_TO_CHANNEL[type]

    @staticmethod
    def dispatch_url(url: str) -> Type[ChannelAdapter] | None:
        for adapter in TYPE_TO_CHANNEL.values():
            if adapter.match(url):
                return adapter

    def __init_subclass__(cls, abstract: bool = False):
        super().__init_subclass__()
        if not abstract:
            assert cls.__name__ not in TYPE_TO_CHANNEL
            TYPE_TO_CHANNEL[cls.__name__] = cls


class DomainMatch(ChannelAdapter, ABC, abstract=True):
    domain: str | tuple[str]

    @classmethod
    def match(cls, url: str) -> bool:
        parts = urlparse(url)
        domain = '.'.join(parts.netloc.split('.')[-2:]).lower()
        domains = cls.domain
        if isinstance(domains, str):
            domains = domains,
        return domain in domains

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        domains = cls.domain
        if isinstance(domains, str):
            domains = domains,
        for domain in domains:
            assert domain not in DOMAIN_TO_CHANNEL
            DOMAIN_TO_CHANNEL[domain] = cls
