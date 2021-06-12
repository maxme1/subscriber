import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import NamedTuple, Optional
from urllib.parse import urlparse

import feedparser
from lxml import html
import requests
from opengraph.opengraph import OpenGraph

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


class YouTube:
    domain = 'youtube.com'

    @staticmethod
    def track(url: str) -> Channel:
        doc = html.fromstring(requests.get(url).content)
        channel_ids = Counter([d.attrib['content'] for d in doc.xpath('//meta[@itemprop="channelId"]')]).most_common(1)
        if not channel_ids:
            raise ValueError('This not a valid youtube channel.')

        channel_id = channel_ids[0][0]
        update_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'

        name = feedparser.parse(update_url)['feed']['title']
        return Channel.get_or_create(update_url=update_url, name=name, type='youtube', defaults={'channel_url': url})

    @staticmethod
    def update(url: str):
        for post in reversed(feedparser.parse(url)['entries']):
            url = post['link']
            yield post['id'], url

    @staticmethod
    def scrape(url: str) -> Content:
        fields = OpenGraph(url, scrape=True)
        return Content(fields['title'], fields['description'], fields['image'])


class VK:
    domain = 'vk.com'

    GROUP_NAME = re.compile(r'^/(\w+)$', flags=re.IGNORECASE)
    REQUEST_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en,en-US;q=0.7,ru;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0',
    }

    @staticmethod
    def track(url: str) -> Channel:
        path = urlparse(url).path
        name = VK.GROUP_NAME.match(path)
        if not name:
            raise ValueError(f'{path} is not a valid channel name.')
        name = name.group(1)
        return Channel.get_or_create(channel_url=url, update_url=url, name=name, type='vk')

    @staticmethod
    def update(url: str):
        doc = html.fromstring(requests.get(url, headers=VK.REQUEST_HEADERS).content)
        for element in reversed(doc.cssselect('.wall_post_cont')):
            i = element.attrib.get('id', '')
            if i.startswith('wpt-'):
                i = i[4:]
                url = f'https://vk.com/wall-{i}'
                yield i, url

    @staticmethod
    def scrape(url: str) -> Content:
        fields = OpenGraph(url, scrape=True)
        return Content(fields['title'], fields['description'])
