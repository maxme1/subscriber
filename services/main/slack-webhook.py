import asyncio
import os
import time

from subscriber.destinations import SlackWebhook
from subscriber.entrypoints import init, run_destination

init()
# FIXME: waiting for rabbit
time.sleep(10)
asyncio.run(run_destination(SlackWebhook(), os.environ['RABBIT_URL']))
