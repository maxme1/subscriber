import telebot
from telebot.types import Message

from .utils import get_new_posts
from .trackers import track_youtube, track_vk
from . import token

bot = telebot.TeleBot(token.token)
handler = bot.message_handler


@handler(commands=['youtube'])
def youtube(message: Message):
    try:
        track_youtube(message.chat.id, message.text.partition(' ')[-1])
    except BaseException as e:
        bot.reply_to(message, str(e))
    else:
        bot.reply_to(message, 'Done')


@handler(commands=['vk'])
def vk(message: Message):
    try:
        track_vk(message.chat.id, message.text.partition(' ')[-1])
    except BaseException as e:
        bot.reply_to(message, str(e))
    else:
        bot.reply_to(message, 'Done')


def notify(user):
    for post in get_new_posts(user):
        bot.send_message(user.identifier, post.url)
