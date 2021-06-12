import re
from typing import Iterable
from urllib.parse import urlparse

import requests
from lxml import html
from opengraph.opengraph import OpenGraph

from .base import Content, ChannelAdapter, ChannelData, PostUpdate


class VK(ChannelAdapter):
    domain = 'vk.com'

    GROUP_NAME = re.compile(r'^/(\w+)$', flags=re.IGNORECASE)
    REQUEST_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en,en-US;q=0.7,ru;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0',
    }

    def track(self, url: str) -> ChannelData:
        path = urlparse(url).path
        name = VK.GROUP_NAME.match(path)
        if not name:
            raise ValueError(f'{path} is not a valid channel name.')
        return ChannelData(url, name.group(1))

    def update(self, url: str) -> Iterable[PostUpdate]:
        doc = html.fromstring(requests.get(url, headers=VK.REQUEST_HEADERS).content)
        for element in reversed(doc.cssselect('.wall_post_cont')):
            i = element.attrib.get('id', '')
            if i.startswith('wpt-'):
                i = i[4:]
                yield PostUpdate(i, f'https://vk.com/wall-{i}')

    def scrape(self, url: str) -> Content:
        fields = OpenGraph(url, scrape=True)
        return Content(fields['title'], fields['description'])
