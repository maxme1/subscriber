import asyncio
import os
import time

from subscriber.entrypoints import init, run_router

init()
# FIXME: waiting for rabbit
time.sleep(10)
asyncio.run(run_router(os.environ['RABBIT_URL']))
