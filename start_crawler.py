import time
from datetime import timedelta

from all_subscriptions_bot.updaters import update_base

UPDATE_DELTA = timedelta(hours=1)

while True:
    update_base(UPDATE_DELTA)
    time.sleep(UPDATE_DELTA.total_seconds())
