import re
from typing import Iterable
from urllib.parse import urlparse

import requests
from lxml import html

from .base import Content, ChannelAdapter, ChannelData, PostUpdate
from ..utils import store_url


class VK(ChannelAdapter):
    domain = 'vk.com'

    GROUP_NAME = re.compile(r'^/(\w+)$', flags=re.IGNORECASE)
    IMAGE_LINK = re.compile(r'background-image: url\((.*)\);')

    def track(self, url: str) -> ChannelData:
        path = urlparse(url).path
        name = VK.GROUP_NAME.match(path)
        if not name:
            raise ValueError(f'{path} is not a valid channel name.')
        return ChannelData(url, name.group(1))

    def update(self, update_url: str, channel: ChannelData) -> Iterable[PostUpdate]:
        doc = html.fromstring(requests.get(update_url).content.decode('utf-8'))
        for element in reversed(doc.cssselect('.wall_post_cont')):
            i = element.attrib.get('id', '')
            if i.startswith('wpt-'):
                i = i[4:]
                yield PostUpdate(i, f'https://vk.com/wall-{i}')

    def scrape(self, post_url: str) -> Content:
        doc = html.fromstring(requests.get(post_url).content.decode('utf-8'))
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
                kw['image'] = store_url(match.group(1))

        return Content(**kw)
