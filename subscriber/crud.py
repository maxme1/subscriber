import logging
from typing import Iterable

from sqlalchemy.orm import Session

from .channels import ChannelAdapter, Content
from .models import Channel, Chat, Post, ChatPost, ChatChannel, ChatPostState, TelegramFile
from .utils import get_or_create

logger = logging.getLogger(__name__)


def subscribe(session: Session, channel: Channel, chat_id):
    chat, _ = get_or_create(session, Chat, identifier=chat_id)
    get_or_create(session, ChatChannel, chat_id=chat.id, channel_id=channel.id)


def track(session: Session, adapter: ChannelAdapter, url: str):
    data = adapter.track(url)
    if data.url is not None:
        url = data.url

    channel, created = get_or_create(
        session, Channel, defaults={'channel_url': url, 'image': wrap_image_hash(session, data.image)},
        update_url=data.update_url, name=data.name, type=adapter.name(),
    )
    return channel, created


def update_channel(session: Session, channel: Channel):
    subscribers = session.query(Chat).where(Chat.channels.contains(channel)).all()
    notify = subscribers and session.query(Post).where(Post.channel == channel).first() is not None

    count = 0
    adapter = ChannelAdapter.dispatch_type(channel.type)
    for update in adapter.update(channel.update_url, channel):
        if session.query(Post).where(
                (Post.identifier == update.id) & (Post.channel_id == channel.id)).first() is not None:
            logger.info('Ignoring an already existing update %s for %s', update.url, channel)
            continue

        content = update.content
        if content is None:
            content = adapter.scrape(update.url)
        if content is None:
            content = Content()

        # create the post
        post = Post(
            identifier=update.id, channel=channel, url=update.url, title=content.title or '',
            image=wrap_image_hash(session, content.image), description=content.description or '',
        )
        session.add(post)
        session.flush()
        # prepare chat posts to be sent to subscribers
        #   but only if the channel was already updated in the past
        if notify:
            session.add_all([
                ChatPost(
                    post_id=post.id, chat_id=chat.id, state=ChatPostState.Pending
                ) for chat in subscribers
            ])
            session.flush()

        logger.info('New post %s for %s', update.url, channel)
        count += 1

    return count


def update_base(session: Session):
    count = 0
    for channel in session.query(Channel).all():
        logger.debug('Updating channel %s', channel)

        try:
            count += update_channel(session, channel)
        except Exception as e:
            logger.error('Error while updating %s (%s): %s: %s', channel.name, channel.type, type(e).__name__, e)

    return count


def get_new_posts(session: Session, chat: Chat):
    posts = session.query(ChatPost).where(
        (ChatPost.chat_id == chat.id) & (ChatPost.state == ChatPostState.Pending))
    for chat_post in posts.all():
        with session.begin_nested():
            post, = session.query(Post).where(Post.id == chat_post.post_id).all()
            message_id, image, image_id = yield post, post.channel, ChannelAdapter.dispatch_type(post.channel.type)

            chat_post.state = ChatPostState.Posted
            chat_post.message_id = message_id
            if image is not None and image.identifier is None and image_id is not None:
                image.identifier = image_id

            session.flush()


def get_channels(session: Session, chat_id) -> Iterable[Channel]:
    user, _ = get_or_create(session, Chat, identifier=chat_id)
    return user.channels


def remove_channel(session: Session, user_id, channel_pk):
    return session.query(ChatChannel).filter(
        ChatChannel.chat.has(Chat.identifier == user_id) & (ChatChannel.channel_id == channel_pk)
    ).delete(synchronize_session=False)


def wrap_image_hash(session: Session, image):
    if image is None:
        return

    file, _ = get_or_create(session, TelegramFile, hash=image)
    return file
