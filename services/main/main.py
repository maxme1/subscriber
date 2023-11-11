import asyncio
import logging
import os

from subscriber.destinations import SlackWebhook, Telegram
from subscriber.entrypoints import init, start

logging.getLogger('telegram').setLevel(logging.CRITICAL)

init()
asyncio.run(start([
    Telegram(os.environ['TELEGRAM_TOKEN']),
    SlackWebhook(),
]))
