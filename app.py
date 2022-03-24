import logging
import os
from datetime import timedelta
import argparse
from logging.handlers import TimedRotatingFileHandler

from subscriber.bot import make_updater

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--crawler', default=1, type=float, help='Crawler interval (hours)')
parser.add_argument('-n', '--notifier', default=600, type=float, help='Notifier interval (seconds)')
args = parser.parse_args()
UPDATE_DELTA = timedelta(hours=args.crawler)
token = os.environ['TOKEN']

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('subscriber')
handler = TimedRotatingFileHandler(f"{os.environ['LOGS_PATH']}/warning.log", when='midnight')
handler.setLevel(logging.WARNING)
logger.addHandler(handler)

updater = make_updater(token, update_interval=args.notifier, crawler_interval=UPDATE_DELTA.total_seconds())
updater.start_polling()
updater.idle()
