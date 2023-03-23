from collections import Counter
from typing import AsyncIterable

import aiohttp
import feedparser
from lxml import html

from ..utils import get_og_tags, url_to_base64
from .interface import ChannelAdapter, ChannelData, Content, PostUpdate


class YouTube(ChannelAdapter):
    domain = 'youtube.com'

    async def track(self, url: str) -> ChannelData:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                body = await response.text()

            doc = html.fromstring(body)
            channel_ids = Counter([
                d.attrib['content'] for d in doc.xpath('//meta[@itemprop="channelId"]')
            ]).most_common(1)
            if not channel_ids:
                raise ValueError('This not a valid youtube channel.')

            tags = get_og_tags(body)
            image = await url_to_base64(tags.get('image'), session)

            channel_id = channel_ids[0][0]
            update_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
            normalized_url = f'https://www.youtube.com/channel/{channel_id}'

            name = feedparser.parse(update_url)['feed']['title']
            return ChannelData(update_url=update_url, name=name, image=image, url=normalized_url)

    async def update(self, update_url: str, name: str) -> AsyncIterable[PostUpdate]:
        for post in reversed(feedparser.parse(update_url)['entries']):
            yield PostUpdate(id=post['id'], url=post['link'])

    async def scrape(self, post_url: str) -> Content:
        async with aiohttp.ClientSession() as session:
            async with session.get(post_url) as response:
                fields = get_og_tags(await response.text())

            return Content(
                title=fields['title'], description=fields['description'],
                image=await url_to_base64(fields['image'], session),
            )
