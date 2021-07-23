import re
from typing import Iterable

from .channels import TYPE_TO_CHANNEL
from .database import Channel, ChannelPost, User, atomic
from .trackers import trigger_update

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
        trigger_update(channel)


@atomic()
def get_new_posts(user: User) -> Iterable[ChannelPost]:
    last_updated = user.last_updated

    for channel in user.channels:
        adapter = TYPE_TO_CHANNEL[channel.type]()

        for post in ChannelPost.select().where(ChannelPost.channel == channel).where(
                ChannelPost.created > user.last_updated).order_by(ChannelPost.created):
            yield post, channel, adapter
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


def drop_prefix(x, prefix):
    assert x.startswith(prefix), x
    return x[len(prefix):]
