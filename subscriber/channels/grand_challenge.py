from itertools import count
from typing import Iterable

import requests
from lxml import html

from ..utils import url_to_base64
from .base import ChannelAdapter, ChannelData, Content, PostUpdate


class GrandChallenge(ChannelAdapter):
    domain = 'grand-challenge.org'

    def track(self, url: str) -> ChannelData:
        return ChannelData(
            update_url='https://grand-challenge.org/challenges/all-challenges',
            name='GrandChallenge Competitions',
            url='https://grand-challenge.org'
        )

    def update(self, update_url: str, name: str) -> Iterable[PostUpdate]:
        for page in count(1):
            url = f'https://grand-challenge.org/challenges/all-challenges/?page={page}'
            doc = html.fromstring(requests.get(url).content.decode('utf-8'))
            cards = doc.cssselect('.card.gc-card')
            if not cards:
                break

            for card in cards:
                link, image, body = card.iterchildren()
                link = link.attrib['href']
                image = url_to_base64(image.cssselect('img')[0].attrib['src'])
                title = body.cssselect('.card-title')[0].text_content().strip()

                yield PostUpdate(id=link, url=link, content=Content(title=title, image=image))

    def scrape(self, post_url: str) -> Content:
        raise NotImplementedError
