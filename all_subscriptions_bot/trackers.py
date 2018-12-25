from collections import Counter

import peewee
from lxml import html
import requests

from .database import Channel, atomic, User, REQUEST_HEADERS


def tracker(func):
    @atomic
    def wrapper(user_id, *args, **kwargs):
        channel, created = func(*args, **kwargs)
        if created:
            channel.save()
            channel.trigger_update()

        user, created = User.get_or_create(identifier=user_id)
        if created:
            user.save()
        try:
            user.channels.add(channel)
        except peewee.IntegrityError:
            # TODO: add error message
            pass

    return wrapper


@tracker
def track_youtube(url):
    doc = html.fromstring(requests.get(url, headers=REQUEST_HEADERS).content)
    channel_id = Counter(doc.xpath('//@data-channel-external-id')).most_common(1)[0][0]
    url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
    return Channel.get_or_create(url=url, type='YouTube')


@tracker
def track_vk(url):
    return Channel.get_or_create(url=url, type='vk')
