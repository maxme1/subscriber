import re
from io import BytesIO
from typing import AsyncIterable
from urllib.parse import urlparse

import feedparser
from aiohttp import ClientSession

from .interface import ChannelData, Content, DomainMatch, PostUpdate


class Twitter(DomainMatch):
    domain = 'twitter.com', 'nitter.cz'

    GROUP_NAME = re.compile(r'^/(\w+)$', flags=re.IGNORECASE)
    TWEET = re.compile(r'^.*/status/\d+$')

    @staticmethod
    def _username(url):
        path = urlparse(url).path
        name = Twitter.GROUP_NAME.match(path)
        if not name:
            raise ValueError(f'{path} is not a valid twitter account.')
        return name.group(1)

    @staticmethod
    async def track(url: str) -> ChannelData:
        name = Twitter._username(url)
        return ChannelData(update_url=url, name=name)

    async def update(self, update_url: str, name: str, session: ClientSession) -> AsyncIterable[PostUpdate]:
        base = 'https://nitter.cz/'
        update_url = f'{base}{name}/rss'

        async with session.get(update_url) as response:
            body = await response.read()

        for post in feedparser.parse(BytesIO(body))['entries']:
            text = post['title_detail']['value']
            identifier = link = post['link']
            assert identifier.startswith(base), identifier
            identifier = identifier.removeprefix(base)
            if identifier.endswith('#m'):
                identifier = identifier.removesuffix('#m')

            yield PostUpdate(id=identifier, url=link, content=Content(description=text))

    async def scrape(self, post_url: str, session: ClientSession) -> Content:
        raise NotImplementedError
