import re
from datetime import datetime
from typing import Iterable

from .database import Channel, ChannelPost, User

URL_REGEX = (
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$'
)
URL_PATTERN = re.compile(URL_REGEX, flags=re.IGNORECASE)


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
