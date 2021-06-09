import re
from collections import Counter
from urllib.parse import urlparse

import feedparser
import peewee
from lxml import html
import requests

from .database import Channel, atomic, User

group_name = re.compile(r'^/(\w+)$', flags=re.IGNORECASE)


def tracker(func):
    @atomic()
    def wrapper(user_id, *args, **kwargs):
        channel, created = func(*args, **kwargs)
        user, _ = User.get_or_create(identifier=user_id)

        if created:
            channel.trigger_update(user.last_updated)

        try:
            user.channels.add(channel)
        except peewee.IntegrityError:
            # TODO: add error message
            pass

    return wrapper


@tracker
def track_youtube(url):
    doc = html.fromstring(requests.get(url).content)
    channel_ids = Counter([d.attrib['content'] for d in doc.xpath('//meta[@itemprop="channelId"]')]).most_common(1)
    if not channel_ids:
        raise ValueError('This not a valid youtube channel.')

    channel_id = channel_ids[0][0]
    update_url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'

    name = feedparser.parse(update_url)['feed']['title']
    return Channel.get_or_create(update_url=update_url, name=name, type='youtube', defaults={'channel_url': url})


@tracker
def track_vk(url):
    path = urlparse(url).path
    name = group_name.match(path)
    if not name:
        raise ValueError(f'{path} is not a valid channel name.')
    name = name.group(1)
    return Channel.get_or_create(channel_url=url, update_url=url, name=name, type='vk')


@tracker
def track_twitter(url):
    path = urlparse(url).path
    name = group_name.match(path)
    if not name:
        raise ValueError(f'{path} is not a valid channel name.')
    name = name.group(1)
    return Channel.get_or_create(channel_url=url, update_url=url, name=name, type='twitter')


TRACKERS = {
    # 'twitter': track_twitter,
    'youtube': track_youtube,
    'vk': track_vk,
}

DOMAIN_TO_TYPE = {
    # 'twitter.com': 'twitter',
    'youtube.com': 'youtube',
    'vk.com': 'vk',
}
