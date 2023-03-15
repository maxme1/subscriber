import logging
from datetime import datetime, timedelta
from typing import Iterable, Sequence
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from .base import db, get_or_create
from .channels.base import DOMAIN_TO_CHANNEL, PostUpdate
from .models import (
    ChatPost, ChatPostState, ChatTable, ChatToSource, File, FileTable, Identifier, Post, PostTable, Source, SourceTable
)
from .utils import store_base64

logger = logging.getLogger(__name__)


def subscribe(chat_id: Identifier, chat_type: str, url: str):
    parts = urlparse(url)

    domain = '.'.join(parts.netloc.split('.')[-2:]).lower()
    if domain not in DOMAIN_TO_CHANNEL:
        return f'Unknown domain: {domain}'

    adapter = DOMAIN_TO_CHANNEL[domain]()

    try:
        data = adapter.track(url)
        if data.url is not None:
            url = data.url

        with db() as session:
            chat, _ = get_or_create(session, ChatTable, identifier=chat_id, type=chat_type)
            source, _ = get_or_create(
                session, SourceTable, defaults={'url': url, 'image': wrap_base64_to_hash(session, data.image)},
                update_url=data.update_url, name=data.name, type=adapter.name(),
            )
            get_or_create(session, ChatToSource, chat_id=chat.id, source_id=source.id)

        return 'Done'

    except Exception:
        logger.exception('Exception while subscribing')
        return 'An unknown error occurred'


def unsubscribe(chat_id: str, source_pk: int):
    with db() as session:
        return session.query(ChatToSource).filter(
            ChatToSource.chat.has(ChatTable.identifier == chat_id) & (ChatToSource.source_id == source_pk)
        ).delete(synchronize_session=False)


def list_chat_sources(chat_id: Identifier, chat_type: str) -> Sequence[Source]:
    with db() as session:
        chat, _ = get_or_create(session, ChatTable, identifier=str(chat_id), type=chat_type)
        return [Source(pk=c.id, name=c.name, type=c.type, update_url=c.update_url) for c in chat.sources]


def list_all_sources() -> list[tuple[bool, Source]]:
    with db() as session:
        sources = session.query(SourceTable).all()
        return [
            (
                session.query(PostTable).where(PostTable.source == s).first() is not None,
                Source(pk=s.id, name=s.name, type=s.type, update_url=s.update_url),
            ) for s in sources
        ]


def keep(message_id: Identifier):
    with db() as session:
        post = session.query(ChatPost).where(ChatPost.message_id == message_id).first()
        if post is not None:
            post.state = ChatPostState.Keeping


def save_post(source: Source, update: PostUpdate, notify: bool):
    source_id = source.pk

    with db() as session:
        if session.query(PostTable).where(
                (PostTable.identifier == update.id) & (PostTable.source_id == source_id)
        ).first() is not None:
            logger.info('Ignoring an existing update %s for %s (%s)', update.id, source.name, source.type)
            return

        post_entry = PostTable(
            identifier=update.id, source_id=source_id, url=update.url, title=update.content.title or '',
            image=wrap_base64_to_hash(session, update.content.image), description=update.content.description or '',
        )
        session.add(post_entry)
        session.flush()
        # prepare chat posts to be sent to subscribers
        #   but only if the channel was already updated in the past
        if notify:
            source_entry = session.query(SourceTable).where(SourceTable.id == source_id).first()
            image = post_entry.image or source_entry.image
            post = Post(
                title=post_entry.title, description=post_entry.description, url=post_entry.url,
                image=None if image is None else File(internal=image.internal, telegram=image.telegram),
            )
            for chat in source_entry.chats:
                yield chat.identifier, chat.type, chat.id, post_entry.id, post


def save_chat_post(chat_pk: int, post_pk: int, message_id: Identifier):
    with db() as session:
        session.add(ChatPost(post_id=post_pk, chat_id=chat_pk, message_id=message_id, state=ChatPostState.Pending))
        session.flush()


def get_old_posts() -> Iterable[tuple[str, Identifier, Identifier]]:
    with db() as session:
        outdated = session.query(ChatPost).where(ChatPost.state == ChatPostState.Posted).where(
            ChatPost.post.has(ChatPost.created < datetime.utcnow() - timedelta(days=1))
        )

        for chat_post in outdated.all():
            yield chat_post.chat.type, chat_post.chat.identifier, chat_post.message_id

            chat_post.state = ChatPostState.Deleted
            session.flush()


def wrap_base64_to_hash(session: Session, image):
    if image is None:
        return

    digest = store_base64(image)
    file, _ = get_or_create(session, FileTable, internal=digest)
    return file
