from collections import Counter
from typing import Iterable

import feedparser
from lxml import html
import requests
from opengraph.opengraph import OpenGraph

from .base import Content, ChannelData, ChannelAdapter, PostUpdate


class YouTube(ChannelAdapter):
    domain = 'youtube.com'

    def track(self, url: str) -> ChannelData:
        doc = html.fromstring(requests.get(url).content)
        channel_ids = Counter([d.attrib['content'] for d in doc.xpath('//meta[@itemprop="channelId"]')]).most_common(1)
        if not channel_ids:
            raise ValueError('This not a valid youtube channel.')

        channel_id = channel_ids[0][0]
        update_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'

        name = feedparser.parse(update_url)['feed']['title']
        return ChannelData(update_url, name)

    def update(self, url: str, channel: ChannelData) -> Iterable[PostUpdate]:
        for post in reversed(feedparser.parse(url)['entries']):
            yield PostUpdate(post['id'], post['link'])

    def scrape(self, url: str) -> Content:
        fields = OpenGraph(url, scrape=True)
        return Content(fields['title'], fields['description'], fields['image'])
