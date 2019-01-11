from urllib.parse import urlparse
import logging

from telegram import Message, Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, RegexHandler, CallbackQueryHandler, MessageHandler, Filters

from .utils import get_new_posts, URL_PATTERN, get_channels, remove_channel
from .trackers import TRACKERS, DOMAIN_TO_TYPE


def run_tracker(message: Message, command: str, *args, **kwargs):
    try:
        TRACKERS[command](message.chat.id, *args, **kwargs)
    except BaseException as e:
        message.reply_text(str(e), quote=True)
    else:
        message.reply_text('Done', quote=True)


def start(bot: Bot, update: Update):
    bot.send_message(update.message.chat.id, 'Hi! Send me a link to a channel and I will subscribe you to it.')


def link(bot: Bot, update: Update):
    message = update.message
    url = message.text.strip().lower()
    parts = urlparse(url)

    domain = '.'.join(parts.netloc.split('.')[-2:])
    if domain not in DOMAIN_TO_TYPE:
        return message.reply_text(f'Unknown domain: {domain}', quote=True)

    run_tracker(message, DOMAIN_TO_TYPE[domain], url)


def list_channels(bot: Bot, update: Update):
    message = update.message
    channels = '\n'.join(map(str, get_channels(message.chat.id)))
    if not channels:
        channels = 'You have no subscriptions'
    message.reply_text(channels)


def make_keyboard(user_id):
    buttons = [InlineKeyboardButton(str(c), callback_data=c.id) for c in get_channels(user_id)]
    if not buttons:
        return 'You have no subscriptions', None

    return 'Chose a channel to delete', InlineKeyboardMarkup([buttons[i:i + 2] for i in range(0, len(buttons), 2)])


def delete(bot: Bot, update: Update):
    message = update.message
    text, markup = make_keyboard(message.chat.id)
    message.reply_text(text, reply_markup=markup)


def button_callback(bot: Bot, update: Update):
    query = update.callback_query
    message = query.message
    user_id = message.chat.id
    remove_channel(user_id, query.data)

    text, markup = make_keyboard(user_id)
    bot.edit_message_text(text=text, chat_id=user_id, message_id=message.message_id, reply_markup=markup)


def notify(bot, user):
    for post in get_new_posts(user):
        bot.send_message(user.identifier, post.url)


def fallback(bot: Bot, update: Update):
    update.message.reply_text('Unknown command', quote=True)


def on_error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
REQUEST_KWARGS = {
    'proxy_url': 'https://195.222.106.135:42374/',
}


def make_updater(token) -> Updater:
    updater = Updater(token=token, request_kwargs=REQUEST_KWARGS)
    dispatcher = updater.dispatcher
    dispatcher.add_error_handler(on_error)

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(RegexHandler(URL_PATTERN, link))

    dispatcher.add_handler(CommandHandler('list', list_channels))

    dispatcher.add_handler(CommandHandler('delete', delete))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    dispatcher.add_handler(MessageHandler(Filters.all, fallback))

    return updater
