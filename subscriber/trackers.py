import logging
from datetime import datetime

import peewee

from .channels import ChannelAdapter, TYPE_TO_CHANNEL
from .channels.base import Content
from .database import atomic, User, Channel, ChannelPost

logger = logging.getLogger(__name__)


@atomic()
def track(user_id, channel: ChannelAdapter, url: str):
    data = channel.track(url)
    if data.url is not None:
        url = data.url

    channel, created = Channel.get_or_create(
        update_url=data.update_url, name=data.name, type=channel.name(),
        defaults={'channel_url': url, 'image': data.image}
    )
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

    adapter: ChannelAdapter = TYPE_TO_CHANNEL[channel.type]()
    for update in adapter.update(channel.update_url, channel):
        if ChannelPost.select().where(ChannelPost.identifier == update.id, ChannelPost.channel == channel):
            continue

        content = update.content
        if content is None:
            content = adapter.scrape(update.url)
        if content is None:
            content = Content()
        post = ChannelPost(
            identifier=update.id, url=update.url, channel=channel,
            title=content.title or '', image=content.image or '',
            description=content.description or ''
        )
        if created is not None:
            post.created = created
        post.save()
        logger.debug('New post %s for %s', update.url, channel)
