import re
from datetime import datetime
from typing import Iterable

from .database import Channel, ChannelPost, User, atomic

URL_REGEX = (
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$'
)
URL_PATTERN = re.compile(URL_REGEX, flags=re.IGNORECASE)


def update_base():
    for channel in Channel.select():  # .where(Channel.last_updated <= datetime.now() - update_delta):
        channel.trigger_update()


@atomic()
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


def get_channels(user_id) -> Iterable[Channel]:
    user, _ = User.get_or_create(identifier=user_id)
    return user.channels


@atomic()
def remove_channel(user_id, channel_pk):
    user = User.get(identifier=user_id)
    channel = Channel.get(id=channel_pk)
    user.channels.remove(channel)
    user.save()
    return channel
