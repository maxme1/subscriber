import asyncio
import os

from subscriber.destinations import SlackWebhook
from subscriber.entrypoints import init, run_destination

init()
asyncio.run(run_destination(SlackWebhook(), os.environ['RABBIT_URL']))
