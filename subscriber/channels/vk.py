import re
from typing import Iterable
from urllib.parse import urlparse

import requests
from lxml import html

from .base import Content, ChannelAdapter, ChannelData, PostUpdate


class VK(ChannelAdapter):
    domain = 'vk.com'

    GROUP_NAME = re.compile(r'^/(\w+)$', flags=re.IGNORECASE)
    IMAGE_LINK = re.compile(r'background-image: url\((.*)\);')
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

    def update(self, update_url: str, channel: ChannelData) -> Iterable[PostUpdate]:
        doc = html.fromstring(requests.get(update_url, headers=VK.REQUEST_HEADERS).content)
        for element in reversed(doc.cssselect('.wall_post_cont')):
            i = element.attrib.get('id', '')
            if i.startswith('wpt-'):
                i = i[4:]
                yield PostUpdate(i, f'https://vk.com/wall-{i}')

    def scrape(self, post_url: str) -> Content:
        doc = html.fromstring(requests.get(post_url, headers=VK.REQUEST_HEADERS).content)
        _, i = post_url.split('/wall-')
        post, = [x for x in doc.cssselect(f'div[data-post-id="-{i}"]')]
        kw = {}

        text = post.cssselect('.wall_post_text')
        if text:
            kw['description'] = text[0].text_content()

        image = post.cssselect('.page_post_thumb_wrap')
        if image:
            image = image[0]
            match = VK.IMAGE_LINK.search(image.attrib['style'])
            if match:
                kw['image'] = match.group(1)

        return Content(**kw)
