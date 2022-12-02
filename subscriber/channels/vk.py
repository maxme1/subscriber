import re
from typing import Iterable
from urllib.parse import urlparse

import requests
from lxml import html

from .base import Content, ChannelAdapter, ChannelData, PostUpdate
from ..utils import url_to_base64


class VK(ChannelAdapter):
    domain = 'vk.com'

    GROUP_NAME = re.compile(r'^/(\w+)$', flags=re.IGNORECASE)
    IMAGE_LINK = re.compile(r'background-image: url\((.*)\);')

    def track(self, url: str) -> ChannelData:
        path = urlparse(url).path
        name = VK.GROUP_NAME.match(path)
        if not name:
            raise ValueError(f'{path} is not a valid channel name.')
        return ChannelData(update_url=url, name=name.group(1))

    def update(self, update_url: str, name: str) -> Iterable[PostUpdate]:
        visited = set()
        doc = html.fromstring(requests.get(update_url).content.decode('utf-8'))
        for element in reversed(doc.cssselect('[data-post-id]')):
            i = element.attrib.get('data-post-id', '')
            if i.startswith('-') and i not in visited:
                visited.add(i)
                yield PostUpdate(id=i[1:], url=f'https://vk.com/wall{i}', content=Content())

    def scrape(self, post_url: str) -> Content:
        return Content()

        doc = html.fromstring(requests.get(post_url).content.decode('utf-8'))
        _, i = post_url.split('/wall-')
        post, = [x for x in doc.cssselect('.wi_body')]
        kw = {}

        text = post.cssselect('.pi_text')
        if text:
            kw['description'] = text[0].text_content()

        image = post.cssselect(f'.thumb_link>[data-src_big]')
        if image:
            image = image[0]
            kw['image'] = url_to_base64(image.attrib['data-src_big'])

        return Content(**kw)
