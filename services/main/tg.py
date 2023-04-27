import asyncio
import logging
import os

from subscriber.destinations import Telegram
from subscriber.entrypoints import init, run_destination

init()
logging.getLogger('telegram').setLevel(logging.CRITICAL)
asyncio.run(run_destination(Telegram(os.environ['TELEGRAM_TOKEN']), os.environ['RABBIT_URL']))
