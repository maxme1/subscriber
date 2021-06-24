from abc import ABC, abstractmethod
from typing import NamedTuple, Optional

from .database import Channel

TYPE_TO_CHANNEL = {}
DOMAIN_TO_CHANNEL = {}


class Content(NamedTuple):
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None


class ChannelAdapter(ABC):
    domain: str

    @abstractmethod
    def track(self, url: str) -> Channel:
        pass

    @abstractmethod
    def update(self, url: str):
        pass

    @abstractmethod
    def scrape(self, url: str) -> Content:
        pass

    def __init_subclass__(cls, **kwargs):
        assert cls.__name__ not in TYPE_TO_CHANNEL
        assert cls.domain not in DOMAIN_TO_CHANNEL
        TYPE_TO_CHANNEL[cls.__name__] = cls
        DOMAIN_TO_CHANNEL[cls.domain] = cls
