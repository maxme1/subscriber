import re
from collections import Counter
from io import BytesIO
from typing import AsyncIterable

import feedparser
import requests
from aiohttp import ClientSession

from ..utils import get_og_tags, url_to_base64
from .interface import ChannelData, Content, DomainMatch, PostUpdate, VisibleError


class YouTube(DomainMatch):
    domain = 'youtube.com'
    CHANNEL_ID_PATTERN = re.compile(r'"browseId":\s*"([^"]+)"')

    @classmethod
    async def track(cls, url: str) -> ChannelData:
        body = (await aget(url)).text
        channel_ids = Counter(x.group(1) for x in cls.CHANNEL_ID_PATTERN.finditer(body)).most_common(1)
        if not channel_ids:
            raise VisibleError('This not a valid youtube channel.')

        tags = get_og_tags(body)
        async with ClientSession() as session:
            image = await url_to_base64(tags.get('image'), session)

        channel_id = channel_ids[0][0]
        update_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
        normalized_url = f'https://www.youtube.com/channel/{channel_id}'

        name = feedparser.parse(update_url)['feed']['title']
        return ChannelData(update_url=update_url, name=name, image=image, url=normalized_url)

    async def update(self, update_url: str, name: str, session: ClientSession) -> AsyncIterable[PostUpdate]:
        async with session.get(update_url) as response:
            body = await response.read()

        for post in reversed(feedparser.parse(BytesIO(body))['entries']):
            yield PostUpdate(id=post['id'], url=post['link'])

    async def scrape(self, post_url: str, session: ClientSession) -> Content:
        fields = get_og_tags((await aget(post_url)).text)

        if 'title' in fields:
            return Content(
                title=fields['title'], description=fields['description'],
                image=await url_to_base64(fields['image'], session),
            )

        return Content()


# TODO: make this truly async
async def aget(url):
    return requests.get(url)
