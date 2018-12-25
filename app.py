from datetime import timedelta
import time
import argparse
from threading import Thread

from all_subscriptions_bot.utils import update_base
from all_subscriptions_bot.bot import bot, notify
from all_subscriptions_bot.database import User

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--crawler', default=1, type=float, help='Crawler interval (hours)')
parser.add_argument('-n', '--notifier', default=60, type=float, help='Notifier interval (seconds)')
args = parser.parse_args()
UPDATE_DELTA = timedelta(hours=args.crawler)


def crawler():
    while True:
        update_base(UPDATE_DELTA)
        time.sleep(UPDATE_DELTA.total_seconds())


def notifier():
    while True:
        for user in User.select():
            notify(user)

        time.sleep(args.notifier)


Thread(target=crawler).start()
Thread(target=notifier).start()
bot.polling()
