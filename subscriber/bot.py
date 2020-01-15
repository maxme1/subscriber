from urllib.parse import urlparse
import logging

from telegram import Message, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext, Job

from subscriber.database import User
from .utils import get_new_posts, URL_PATTERN, get_channels, remove_channel
from .trackers import TRACKERS, DOMAIN_TO_TYPE


def run_tracker(message: Message, command: str, *args, **kwargs):
    try:
        TRACKERS[command](message.chat.id, *args, **kwargs)
    except BaseException as e:
        message.reply_text(str(e), quote=True)
        raise
    else:
        message.reply_text('Done', quote=True)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(update.message.chat.id, 'Hi! Send me a link to a channel and I will subscribe you to it.')


def link(update: Update, context: CallbackContext):
    message = update.message
    url = message.text.strip().lower()
    parts = urlparse(url)

    domain = '.'.join(parts.netloc.split('.')[-2:])
    if domain not in DOMAIN_TO_TYPE:
        return message.reply_text(f'Unknown domain: {domain}', quote=True)

    run_tracker(message, DOMAIN_TO_TYPE[domain], url)


def list_channels(update: Update, context: CallbackContext):
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


def delete(update: Update, context: CallbackContext):
    message = update.message
    text, markup = make_keyboard(message.chat.id)
    message.reply_text(text, reply_markup=markup)


def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    message = query.message
    user_id = message.chat.id
    remove_channel(user_id, query.data)

    text, markup = make_keyboard(user_id)
    context.bot.edit_message_text(text=text, chat_id=user_id, message_id=message.message_id, reply_markup=markup)


def send_new_posts(context: CallbackContext):
    for user in User.select():
        for post in get_new_posts(user):
            context.bot.send_message(user.identifier, post.url)


def fallback(update: Update, context: CallbackContext):
    update.message.reply_text('Unknown command', quote=True)


def on_error(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def make_updater(token, update_interval) -> Updater:
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue
    dispatcher.add_error_handler(on_error)

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.regex(URL_PATTERN), link))

    dispatcher.add_handler(CommandHandler('list', list_channels))

    dispatcher.add_handler(CommandHandler('delete', delete))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    dispatcher.add_handler(MessageHandler(Filters.all, fallback))

    job_queue.run_repeating(send_new_posts, interval=update_interval, first=0)

    return updater
