import logging
from itertools import count
from typing import AsyncIterable

import aiohttp
from lxml import html

from ..utils import url_to_base64
from .interface import ChannelAdapter, ChannelData, Content, PostUpdate

logger = logging.getLogger(__name__)


class GrandChallenge(ChannelAdapter):
    domain = 'grand-challenge.org'

    @staticmethod
    async def track(url: str) -> ChannelData:
        return ChannelData(
            update_url='https://grand-challenge.org/challenges/all-challenges',
            name='GrandChallenge Competitions',
            url='https://grand-challenge.org'
        )

    async def update(self, update_url: str, name: str) -> AsyncIterable[PostUpdate]:
        async with aiohttp.ClientSession() as session:
            for page in count(1):
                url = f'https://grand-challenge.org/challenges/?page={page}'
                async with session.get(url) as response:
                    if page == 1 and response.status == 404:
                        logger.error('The update link is broken')
                        break

                    doc = html.fromstring(await response.text())

                cards = doc.cssselect('.card.gc-card')
                if not cards:
                    break

                for card in cards:
                    link, image, body = card.iterchildren()
                    link = link.attrib['href']
                    image = await url_to_base64(image.cssselect('img')[0].attrib['src'], session)
                    title = body.cssselect('.card-title')[0].text_content().strip()

                    yield PostUpdate(id=link, url=link, content=Content(title=title, image=image))

    async def scrape(self, post_url: str) -> Content:
        raise NotImplementedError
