from threading import Thread

from all_subscriptions_bot.handlers import bot

Thread(target=bot.polling).start()
