import logging
from datetime import datetime

import peewee

from .channels import ChannelAdapter, TYPE_TO_CHANNEL
from .database import atomic, User, Channel, ChannelPost

logger = logging.getLogger(__name__)


@atomic()
def track(user_id, channel: ChannelAdapter, url: str):
    channel, created = channel.track(url)
    user, _ = User.get_or_create(identifier=user_id)

    if created:
        trigger_update(channel, user.last_updated)

    try:
        user.channels.add(channel)
    except peewee.IntegrityError:
        # TODO: add error message
        pass


@atomic()
def trigger_update(channel: Channel, created: datetime = None):
    channel.last_updated = datetime.now()
    channel.save()
    logger.debug('Updating channel %s', channel)

    adapter: ChannelAdapter = TYPE_TO_CHANNEL[channel.type]

    for i, url in adapter.update(channel.update_url):
        if ChannelPost.select().where(ChannelPost.identifier == i, ChannelPost.channel == channel):
            continue

        content = adapter.scrape(url)
        post = ChannelPost(
            identifier=i, url=url, channel=channel,
            title=content.title or '', image=content.image or '',
            description=content.description or ''
        )
        if created is not None:
            post.created = created
        post.save()
        logger.debug('New post %s for %s', url, channel)
