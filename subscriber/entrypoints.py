import asyncio
import json
import logging
import os
from collections import defaultdict
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import aio_pika
from sqlalchemy_utils import create_database, database_exists

from .base import make_engine
from .crud import get_old_posts, list_all_sources, save_chat_post, save_post
from .destinations import Destination
from .models import Base, Post, Source
from .sources import ChannelAdapter, PostUpdate

logger = logging.getLogger(__name__)
ROUTER_QUEUE = 'router'


async def run_source(rabbit_url):
    # todo: will this consume all ram?
    # todo: fill from the database?
    visited = defaultdict(set)

    connection = await aio_pika.connect_robust(rabbit_url, heartbeat=300)
    async with connection:
        channel = await connection.channel()

        while True:
            for notify, source in list_all_sources():
                adapter = ChannelAdapter.dispatch_type(source.type)
                async for update in adapter.update(source.update_url, source.name):
                    if update.id in visited[source.pk]:
                        logger.debug('Post exists: %s for %s (%s)', update.id, source.name, source.type)
                        continue

                    logger.info('New post: %s for %s (%s)', update.id, source.name, source.type)
                    visited[source.pk].add(update.id)

                    content = update.content
                    if content is None:
                        update.content = await adapter.scrape(update.url)

                    await channel.default_exchange.publish(
                        aio_pika.Message(body=json.dumps([source.json(), update.json(), notify]).encode()),
                        routing_key=ROUTER_QUEUE,
                    )

            await asyncio.sleep(600)


async def delete_old_posts(channel):
    while True:
        for chat_type, chat_id, message_id in get_old_posts():
            await channel.default_exchange.publish(
                # TODO: use an Enum
                aio_pika.Message(body=json.dumps(['remove', chat_id, message_id]).encode()),
                routing_key=chat_type,
            )

        await asyncio.sleep(3600)


async def run_router(rabbit_url):
    connection = await aio_pika.connect_robust(rabbit_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        # old posts removal
        asyncio.create_task(delete_old_posts(channel))

        # new posts notification
        queue = await channel.declare_queue(ROUTER_QUEUE)
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    source, update, notify = json.loads(message.body)
                    source, update = Source.parse_raw(source), PostUpdate.parse_raw(update)
                    logger.debug('Got update %s for source %s (%s)', update.id, source.name, source.type)

                    for chat_id, chat_type, chat_pk, post_pk, post in save_post(source, update, notify):
                        await channel.default_exchange.publish(
                            # TODO: use an Enum
                            aio_pika.Message(body=json.dumps([
                                'notify', chat_id, chat_pk, post_pk, post.json()
                            ]).encode()), routing_key=chat_type,
                        )


async def run_destination(destination: Destination, rabbit_url: str):
    await destination.start()

    connection = await aio_pika.connect_robust(rabbit_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue(destination.name())

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    cmd, chat_id, *args = json.loads(message.body)

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

                    else:
                        raise TypeError(cmd)

    await destination.stop()


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
