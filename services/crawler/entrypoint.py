import asyncio
import os

from subscriber.entrypoints import init, run_source

init()
asyncio.run(run_source(os.environ['RABBIT_URL']))
