from abc import ABC, abstractmethod
from typing import NamedTuple, Optional, Iterable

TYPE_TO_CHANNEL = {}
DOMAIN_TO_CHANNEL = {}


class Content(NamedTuple):
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None


class ChannelData(NamedTuple):
    # the url used to scrape for updates
    update_url: str
    # the channel name
    name: str
    # an optional image URL
    image: str = ''
    # a standardized channel url (optional)
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
        """ Get essential channel information based on the provided url """

    @abstractmethod
    def update(self, update_url: str, channel: ChannelData) -> Iterable[PostUpdate]:
        """ Get the list of posts for a channel """

    @abstractmethod
    def scrape(self, post_url: str) -> Content:
        """ Get additional information for a post. Invoked only if post_update.content is None """

    @classmethod
    def name(cls):
        return cls.__name__

    def __init_subclass__(cls, **kwargs):
        assert cls.__name__ not in TYPE_TO_CHANNEL
        assert cls.domain not in DOMAIN_TO_CHANNEL
        TYPE_TO_CHANNEL[cls.__name__] = cls
        DOMAIN_TO_CHANNEL[cls.domain] = cls
