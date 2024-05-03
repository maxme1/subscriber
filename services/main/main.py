import asyncio
import logging

from subscriber.destinations import SlackWebhook, Telegram
from subscriber.entrypoints import init, start
from subscriber.settings import config


logging.getLogger('telegram').setLevel(logging.CRITICAL)

init()
asyncio.run(start([
    Telegram(config.telegram_token),
    SlackWebhook(),
]))
