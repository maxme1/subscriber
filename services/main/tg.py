import asyncio
import os
import time

from subscriber.destinations import Telegram
from subscriber.entrypoints import init, run_destination

init()
# FIXME: waiting for rabbit
time.sleep(10)
asyncio.run(run_destination(Telegram(os.environ['TELEGRAM_TOKEN']), os.environ['RABBIT_URL']))
