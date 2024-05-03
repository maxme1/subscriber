from io import BytesIO
from typing import AsyncIterable

import feedparser
from aiohttp import ClientSession

from .interface import ChannelAdapter, ChannelData, Content, PostUpdate


class RSS(ChannelAdapter):
    @classmethod
    def match(cls, url: str) -> bool:
        return url.endswith('.xml')

    @classmethod
    async def track(cls, url: str) -> ChannelData:
        feed = feedparser.parse(url)['feed']
        return ChannelData(update_url=url, name=feed['title'], url=url)

    async def update(self, update_url: str, name: str, session: ClientSession) -> AsyncIterable[PostUpdate]:
        async with session.get(update_url) as response:
            body = await response.read()

        for post in reversed(feedparser.parse(BytesIO(body))['entries']):
            yield PostUpdate(id=post['id'], url=post['link'], content=Content(
                title=post['title'], description=post['summary'],
            ))

    async def scrape(self, post_url: str, session: ClientSession) -> Content:
        raise NotImplementedError
