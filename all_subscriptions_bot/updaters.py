from datetime import datetime, timedelta
from collections import Counter
from typing import Iterable

import peewee
import feedparser
from lxml import html
import requests

from .database import Channel, ChannelPost, atomic, User


@atomic
def track_youtube(user_id, url):
    b = html.fromstring(requests.get(url).content)
    channel_id = Counter(b.xpath('//@data-channel-external-id')).most_common(1)[0][0]
    url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
    channel, _ = Channel.get_or_create(url=url, name=channel_id, type='YouTube')
    user, _ = User.get_or_create(identifier=user_id)
    try:
        user.channels.add(channel)
    except peewee.IntegrityError:
        # TODO: add error message
        pass


@atomic
def update_youtube(channel: Channel):
    channel.last_updated = datetime.now()
    channel.save()

    count = 0
    for post in feedparser.parse(channel.url)['entries']:
        try:
            ChannelPost(
                identifier=post['id'], title=post['title'], url=post['link'],
                image_url=post['media_thumbnail'][0]['url'], description=post['summary'],
                channel=channel
            ).save()
            count += 1
        except peewee.IntegrityError:
            pass

    return count


UPDATERS = {'YouTube': update_youtube}


def update_base(update_delta):
    count = 0
    for channel in Channel.select().where(Channel.last_updated <= datetime.now() - update_delta):
        count += UPDATERS[channel.type](channel)

    return count


@atomic
def get_new_posts(user: User) -> Iterable[ChannelPost]:
    for channel in user.channels:
        for post in ChannelPost.select().where(ChannelPost.channel == channel).where(
                ChannelPost.created > user.last_updated).order_by(ChannelPost.created):
            yield post
            user.last_updated = post.created
            user.save()
