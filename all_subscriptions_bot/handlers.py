import telebot
from telebot.types import Message

from .updaters import track_youtube, get_new_posts
from . import token

bot = telebot.TeleBot(token.token)
handler = bot.message_handler


@handler(commands=['add'])
def send_welcome(message: Message):
    try:
        track_youtube(message.chat.id, message.text.partition(' ')[-1])
    except BaseException:
        bot.reply_to(message, 'Something bad happened')
    else:
        bot.reply_to(message, 'Done')


def notify(user):
    for post in get_new_posts(user):
        bot.send_message(user.identifier, post.url)
