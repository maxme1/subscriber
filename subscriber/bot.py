import traceback
from contextlib import suppress
from datetime import datetime, timedelta
from urllib.parse import urlparse
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, TelegramError, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

from .channels import DOMAIN_TO_CHANNEL
from .database import User, Task
from .utils import get_new_posts, URL_PATTERN, get_channels, remove_channel, update_base, drop_prefix
from .trackers import track

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(update.message.chat.id, 'Hi! Send me a link to a channel and I will subscribe you to it.')


def link(update: Update, context: CallbackContext):
    message = update.message
    url = message.text.strip()
    parts = urlparse(url)

    domain = '.'.join(parts.netloc.split('.')[-2:]).lower()
    if domain not in DOMAIN_TO_CHANNEL:
        return message.reply_text(f'Unknown domain: {domain}', quote=True)

    try:
        track(message.chat.id, DOMAIN_TO_CHANNEL[domain](), url)
    except BaseException:
        traceback.print_exc()
        message.reply_text('An unknown error occurred', quote=True)
        raise
    else:
        message.reply_text('Done', quote=True)


def list_channels(update: Update, context: CallbackContext):
    message = update.message
    channels = '\n'.join(map(str, get_channels(message.chat.id)))
    if not channels:
        channels = 'You have no subscriptions'
    message.reply_text(channels)


def make_keyboard(user_id):
    buttons = [InlineKeyboardButton(str(c), callback_data=f'DELETE:{c.id}') for c in get_channels(user_id)]
    if not buttons:
        return 'You have no subscriptions', None

    return 'Chose a channel to delete', InlineKeyboardMarkup([buttons[i:i + 2] for i in range(0, len(buttons), 2)])


def delete(update: Update, context: CallbackContext):
    message = update.message
    text, markup = make_keyboard(message.chat.id)
    message.reply_text(text, reply_markup=markup)


def delete_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    message = query.message
    user_id = message.chat.id
    remove_channel(user_id, drop_prefix(query.data, 'DELETE:'))

    text, markup = make_keyboard(user_id)
    message.edit_reply_markup(markup)


def keep_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    message = query.message
    with suppress(Task.DoesNotExist):
        Task.get(chat=int(message.chat.id), message=int(message.message_id)).delete_instance()

    message.edit_reply_markup(InlineKeyboardMarkup.from_button(
        InlineKeyboardButton('Dismiss', callback_data='DISMISS')))


def dismiss_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    message = query.message
    with suppress(Task.DoesNotExist):
        Task.get(chat=int(message.chat.id), message=int(message.message_id)).delete_instance()

    message.delete()


def send_post(post, user, bot):
    text = f'{post.title}\n{post.description}\n{post.url}'.strip()

    markup = InlineKeyboardMarkup.from_row([
        InlineKeyboardButton('Keep', callback_data='KEEP'),
        InlineKeyboardButton('Dismiss', callback_data='DISMISS'),
    ])

    if post.image:
        message = bot.send_photo(
            user.identifier, post.image, parse_mode=ParseMode.HTML,
            caption=text, reply_markup=markup
        )
    else:
        message = bot.send_message(
            user.identifier, text, reply_markup=markup, parse_mode=ParseMode.HTML,
            disable_web_page_preview=bool(post.title or post.description),
        )

    Task.create(
        chat=int(user.identifier), message=message.message_id,
        when=datetime.now() + timedelta(days=1)
    )


def send_new_posts(context: CallbackContext):
    bot = context.bot
    for user in User.select():
        for post in get_new_posts(user):
            send_post(post, user, bot)


def remove_old_posts(context: CallbackContext):
    bot = context.bot
    for task in Task.select().where(Task.when <= datetime.now()):
        with suppress(TelegramError):
            bot.delete_message(task.chat, task.message)

        task.delete_instance()


def fallback(update: Update, context: CallbackContext):
    update.message.reply_text('Unknown command', quote=True)


def on_error(update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def make_updater(token, update_interval, crawler_interval) -> Updater:
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue
    dispatcher.add_error_handler(on_error)

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.regex(URL_PATTERN), link))

    dispatcher.add_handler(CommandHandler('list', list_channels))

    dispatcher.add_handler(CommandHandler('delete', delete))

    dispatcher.add_handler(CallbackQueryHandler(delete_callback, pattern='DELETE'))
    dispatcher.add_handler(CallbackQueryHandler(keep_callback, pattern='KEEP'))
    dispatcher.add_handler(CallbackQueryHandler(dismiss_callback, pattern='DISMISS'))

    dispatcher.add_handler(MessageHandler(Filters.all, fallback))

    job_queue.run_repeating(send_new_posts, interval=update_interval, first=5)
    job_queue.run_repeating(remove_old_posts, interval=update_interval, first=10)
    job_queue.run_repeating(lambda context: update_base(), interval=crawler_interval, first=15)

    return updater
