import time
from datetime import timedelta
from threading import Thread

from all_subscriptions_bot.database import User
from all_subscriptions_bot.handlers import bot, notify

UPDATE_DELTA = timedelta(hours=1)

Thread(target=bot.polling).start()

while True:
    for user in User.select():
        notify(user)

    time.sleep(UPDATE_DELTA.total_seconds())
