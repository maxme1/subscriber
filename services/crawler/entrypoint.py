import asyncio
import os
import time

from subscriber.entrypoints import init, run_source

init()
# FIXME: waiting for rabbit
time.sleep(10)
asyncio.run(run_source(os.environ['RABBIT_URL']))
