from datetime import datetime
from collections import Counter
from typing import Iterable

import peewee
from lxml import html
import requests

from .database import Channel, ChannelPost, atomic, User


@atomic
def track_youtube(user_id, url):
    b = html.fromstring(requests.get(url).content)
    channel_id = Counter(b.xpath('//@data-channel-external-id')).most_common(1)[0][0]
    url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
    channel, created = Channel.get_or_create(url=url, name=channel_id, type='YouTube')
    if created:
        channel.trigger_update()

    user, _ = User.get_or_create(identifier=user_id)
    try:
        user.channels.add(channel)
    except peewee.IntegrityError:
        # TODO: add error message
        pass


def update_base(update_delta):
    for channel in Channel.select().where(Channel.last_updated <= datetime.now() - update_delta):
        channel.trigger_update()


def get_new_posts(user: User) -> Iterable[ChannelPost]:
    last_updated = user.last_updated

    for channel in user.channels:
        for post in ChannelPost.select().where(ChannelPost.channel == channel).where(
                ChannelPost.created > user.last_updated).order_by(ChannelPost.created):
            yield post
            last_updated = max(last_updated, post.created)

    if last_updated > user.last_updated:
        user.last_updated = last_updated
        user.save()
