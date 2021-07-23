from abc import ABC, abstractmethod
from typing import NamedTuple, Optional, Iterable

TYPE_TO_CHANNEL = {}
DOMAIN_TO_CHANNEL = {}


class Content(NamedTuple):
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None


class ChannelData(NamedTuple):
    update_url: str
    name: str
    image: str = ''
    url: Optional[str] = None


class PostUpdate(NamedTuple):
    id: str
    url: str
    content: Optional[Content] = None


class ChannelAdapter(ABC):
    domain: str
    add_name: bool = False

    @abstractmethod
    def track(self, url: str) -> ChannelData:
        pass

    @abstractmethod
    def update(self, url: str, channel: ChannelData) -> Iterable[PostUpdate]:
        pass

    @abstractmethod
    def scrape(self, url: str) -> Content:
        pass

    @classmethod
    def name(cls):
        return cls.__name__

    def __init_subclass__(cls, **kwargs):
        assert cls.__name__ not in TYPE_TO_CHANNEL
        assert cls.domain not in DOMAIN_TO_CHANNEL
        TYPE_TO_CHANNEL[cls.__name__] = cls
        DOMAIN_TO_CHANNEL[cls.domain] = cls
