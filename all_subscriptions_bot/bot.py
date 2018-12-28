from urllib.parse import urlparse

import telebot
from telebot.types import Message

from .utils import get_new_posts, URL_REGEX
from .trackers import TRACKERS, DOMAIN_TO_TYPE
from . import token

bot = telebot.TeleBot(token.token)
handler = bot.message_handler


def run_tracker(message: Message, command: str, *args, **kwargs):
    try:
        TRACKERS[command](message.chat.id, *args, **kwargs)
    except BaseException as e:
        bot.reply_to(message, str(e))
    else:
        bot.reply_to(message, 'Done')


@handler(commands=['start'])
def start(message: Message):
    bot.send_message(message.chat.id, 'Hi! Send me a link to a channel and I will subscribe you to it.')


@handler(commands=['youtube', 'vk'])
def youtube(message: Message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        return bot.reply_to(message, 'Incorrect command format')

    run_tracker(message, *parts)


@handler(regexp=URL_REGEX)
def link(message: Message):
    url = message.text.strip().lower()
    parts = urlparse(url)

    domain = '.'.join(parts.netloc.split('.')[-2:])
    if domain not in DOMAIN_TO_TYPE:
        return bot.reply_to(message, f'Unknown domain: {domain}')

    run_tracker(message, DOMAIN_TO_TYPE[domain], url)


@handler(content_types=None)
def fallback(message: Message):
    bot.reply_to(message, 'Unknown command')


def notify(user):
    for post in get_new_posts(user):
        bot.send_message(user.identifier, post.url)
