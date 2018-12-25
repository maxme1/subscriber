import time
import argparse

from all_subscriptions_bot.database import User
from all_subscriptions_bot.bot import notify

parser = argparse.ArgumentParser()
parser.add_argument('seconds', type=float)
args = parser.parse_args()

while True:
    for user in User.select():
        notify(user)

    time.sleep(args.seconds)
