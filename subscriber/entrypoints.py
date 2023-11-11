import asyncio
import logging
import os
from asyncio import Queue
from collections import defaultdict
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from aiohttp import ClientSession
from sqlalchemy_utils import create_database, database_exists

from .base import make_engine
from .crud import get_old_posts, list_all_sources, list_sources_and_posts, save_chat_post, save_post, delete
from .destinations import Destination
from .models import Base, Post
from .sources import ChannelAdapter

logger = logging.getLogger(__name__)


async def start(destinations: list[Destination]):
    queue, queues, tasks = Queue(), {}, []
    for dst in destinations:
        q = queues[dst.name()] = Queue()
        tasks.append(run_destination(dst, q))

    await asyncio.gather(
        run_source(queue),
        run_router(queue, queues),
        delete_old_posts(queues),
        *tasks,
    )


async def run_source(queue: Queue):
    # todo: will this consume all ram?
    visited = defaultdict(set)
    visited.update(list_sources_and_posts())

    async with ClientSession() as session:
        while True:
            groups = defaultdict(list)
            for notify, source in list_all_sources():
                groups[source.type].append((notify, source))

            for kind, sources in groups.items():
                adapter = ChannelAdapter.dispatch_type(kind)()

                for notify, source in sources:
                    try:
                        async for update in adapter.update(source.update_url, source.name, session):
                            if update.id in visited[source.pk]:
                                logger.debug('Post exists: %s for %s (%s)', update.id, source.name, source.type)
                                continue

                            logger.info('New post: %s for %s (%s)', update.id, source.name, source.type)
                            visited[source.pk].add(update.id)

                            if update.content is None:
                                update.content = await adapter.scrape(update.url, session)

                            await queue.put((source, update, notify))

                    except Exception as e:
                        logger.error(
                            'An exception while processing %s (%s): %s: %s',
                            source.name, source.type, type(e).__name__, e,
                        )

                # release the allocated resources
                del adapter

            await asyncio.sleep(600)


async def delete_old_posts(queues: dict[str, Queue]):
    while True:
        for chat_type, chat_id, message_id in get_old_posts():
            await queues[chat_type].put(('remove', chat_id, message_id))

        await asyncio.sleep(3600)


async def run_router(updates: Queue, queues: dict[str, Queue]):
    while True:
        source, update, notify = await updates.get()
        logger.debug('Got update %s for source %s (%s)', update.id, source.name, source.type)

        # TODO: without persistence some message might get lost
        for chat_id, chat_type, chat_pk, post_pk, post in save_post(source, update, notify):
            await queues[chat_type].put(('notify', chat_id, chat_pk, post_pk, post.json()))

        updates.task_done()


async def run_destination(destination: Destination, queue: Queue):
    async with destination:
        while True:
            message = await queue.get()
            try:
                cmd, chat_id, *args = message

                if cmd == 'notify':
                    chat_pk, post_pk, post = args
                    post = Post.parse_raw(post)

                    logger.info('Notifying %s about %s', chat_id, post.title or post.description[:20])
                    message_id = await destination.notify(chat_id, post)
                    if message_id is not None:
                        save_chat_post(chat_pk, post_pk, message_id)

                elif cmd == 'remove':
                    message_id, = args

                    logger.info('Removing old post %s from %s', message_id, chat_id)
                    await destination.remove(chat_id, message_id)
                    delete(message_id)

                else:
                    raise TypeError(cmd)

            except BaseException:
                logger.exception('Error while processing message %s', message)
                raise

            queue.task_done()


def init():
    # storage
    storage_path = os.environ.get('STORAGE_PATH')
    if storage_path is not None and not list(Path(storage_path).iterdir()):
        with open(Path(storage_path) / 'config.yml', 'w') as config:
            config.write('hash: sha256\nlevels: [ 1, 31 ]')

    # database
    engine = make_engine()
    if not database_exists(engine.url):
        create_database(engine.url)
        Base.metadata.create_all(engine)

    assert database_exists(engine.url)

    # logging
    logger_ = logging.getLogger('subscriber')
    logger_.setLevel(logging.INFO)
    _add_handler(logger_, logging.StreamHandler(), logging.INFO)
    logs_path = os.environ.get('LOGS_PATH')
    if logs_path is not None:
        _add_handler(
            logger_, TimedRotatingFileHandler(Path(logs_path) / 'warning.log', when='midnight'), logging.WARNING
        )


def _add_handler(logger_, handler, level):
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger_.addHandler(handler)
