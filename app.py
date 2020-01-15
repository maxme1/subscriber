from datetime import timedelta
import time
import argparse
from threading import Thread

from subscriber.utils import update_base
from subscriber.bot import make_updater
# TODO: move to getpass
from subscriber.token import token

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--crawler', default=1, type=float, help='Crawler interval (hours)')
parser.add_argument('-n', '--notifier', default=60, type=float, help='Notifier interval (seconds)')
args = parser.parse_args()
UPDATE_DELTA = timedelta(hours=args.crawler)


# TODO: add a scheduler
def crawler():
    while True:
        update_base(UPDATE_DELTA)
        time.sleep(UPDATE_DELTA.total_seconds())


updater = make_updater(token, args.notifier)
Thread(target=crawler).start()
updater.start_polling()
