from collections import Counter
from typing import Iterable

import feedparser
from lxml import html
import requests

from .base import Content, ChannelData, ChannelAdapter, PostUpdate
from ..utils import get_og_tags, store_url


class YouTube(ChannelAdapter):
    domain = 'youtube.com'

    def track(self, url: str) -> ChannelData:
        body = requests.get(url, cookies=dict(CONSENT='YES+999')).content.decode('utf-8')
        doc = html.fromstring(body)
        channel_ids = Counter([d.attrib['content'] for d in doc.xpath('//meta[@itemprop="channelId"]')]).most_common(1)
        if not channel_ids:
            raise ValueError('This not a valid youtube channel.')

        tags = get_og_tags(body)
        image = store_url(tags.get('image'))

        channel_id = channel_ids[0][0]
        update_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'

        name = feedparser.parse(update_url)['feed']['title']
        return ChannelData(update_url, name, image)

    def update(self, update_url: str, name: str) -> Iterable[PostUpdate]:
        for post in reversed(feedparser.parse(update_url)['entries']):
            yield PostUpdate(post['id'], post['link'])

    def scrape(self, post_url: str) -> Content:
        fields = get_og_tags(requests.get(post_url).content.decode('utf-8'))
        return Content(fields['title'], fields['description'], store_url(fields['image']))
