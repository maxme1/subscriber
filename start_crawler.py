import argparse
import time
from datetime import timedelta

from all_subscriptions_bot.utils import update_base

parser = argparse.ArgumentParser()
parser.add_argument('hours', type=float)
args = parser.parse_args()
UPDATE_DELTA = timedelta(hours=args.hours)

while True:
    update_base(UPDATE_DELTA)
    time.sleep(UPDATE_DELTA.total_seconds())
