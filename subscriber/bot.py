import traceback
from contextlib import suppress
from datetime import datetime, timedelta
from urllib.parse import urlparse
import logging

from sqlalchemy.orm import Session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, TelegramError, ParseMode, Bot
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

from .channels import DOMAIN_TO_CHANNEL, ChannelAdapter
from .crud import get_new_posts, get_channels, remove_channel, track, subscribe, update_base
from .models import Chat, Post, TelegramFile, Channel, ChatPost, ChatPostState
from .ops import delete_message
from .utils import URL_PATTERN, drop_prefix, STORAGE, no_context, with_session

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(update.message.chat.id, 'Hi! Send me a link to a channel and I will subscribe you to it.')


@no_context
@with_session
def link(update: Update, session: Session):
    message = update.message
    url = message.text.strip()
    parts = urlparse(url)

    domain = '.'.join(parts.netloc.split('.')[-2:]).lower()
    if domain not in DOMAIN_TO_CHANNEL:
        return message.reply_text(f'Unknown domain: {domain}', quote=True)

    try:
        channel, _ = track(session, DOMAIN_TO_CHANNEL[domain](), url)
        subscribe(session, channel, message.chat.id)

    except BaseException:
        traceback.print_exc()
        message.reply_text('An unknown error occurred', quote=True)
        raise
    else:
        message.reply_text('Done', quote=True)


@no_context
@with_session
def list_channels(update: Update, session: Session):
    message = update.message
    channels = '\n'.join(map(str, get_channels(session, message.chat.id)))
    if not channels:
        channels = 'You have no subscriptions'
    message.reply_text(channels)


def make_keyboard(user_id, session):
    buttons = [
        InlineKeyboardButton(str(c), callback_data=f'DELETE:{c.id}')
        for c in get_channels(session, user_id)
    ]
    if not buttons:
        return 'You have no subscriptions', None

    return 'Chose a channel to delete', InlineKeyboardMarkup([buttons[i:i + 2] for i in range(0, len(buttons), 2)])


@no_context
@with_session
def delete(update: Update, session: Session):
    message = update.message
    text, markup = make_keyboard(message.chat.id, session)
    message.reply_text(text, reply_markup=markup)


@no_context
@with_session
def delete_callback(update: Update, session: Session):
    query = update.callback_query
    message = query.message
    user_id = message.chat.id
    remove_channel(session, user_id, drop_prefix(query.data, 'DELETE:'))

    text, markup = make_keyboard(session, user_id)
    message.edit_reply_markup(markup)


@no_context
@with_session
def keep_callback(update: Update, session: Session):
    query = update.callback_query
    message = query.message
    post = session.query(ChatPost).where(ChatPost.message_id == message.message_id).first()
    if post is not None:
        post.state = ChatPostState.Keeping

    message.edit_reply_markup(InlineKeyboardMarkup.from_button(
        InlineKeyboardButton('Dismiss', callback_data='DISMISS')))


@with_session
def dismiss_callback(update: Update, context: CallbackContext, session: Session):
    query = update.callback_query
    message = query.message
    post = session.query(ChatPost).where(ChatPost.message_id == message.message_id).first()
    if post is not None:
        post.state = ChatPostState.Deleted

    delete_message(context.bot, message.chat_id, message.message_id)


def send_post(post: Post, channel: Channel, adapter: ChannelAdapter, chat: Chat, bot):
    text = f'{post.title}\n{post.description}\n{post.url}'.strip()
    if adapter.add_name:
        text = f'{channel.name}\n{text}'

    markup = InlineKeyboardMarkup.from_row([
        InlineKeyboardButton('Keep', callback_data='KEEP'),
        InlineKeyboardButton('Dismiss', callback_data='DISMISS'),
    ])

    image: TelegramFile = post.image or channel.image
    chat_it = chat.identifier
    image_id = None

    if image:
        if image.identifier is None:
            with open(STORAGE.resolve(image.hash), 'rb') as img:
                message = bot.send_photo(
                    chat_it, img, parse_mode=ParseMode.HTML,
                    caption=text, reply_markup=markup
                )
                image_id = message.photo[0].file_id

        else:
            message = bot.send_photo(
                chat_it, image.identifier, parse_mode=ParseMode.HTML,
                caption=text, reply_markup=markup
            )

    else:
        message = bot.send_message(
            chat_it, text, reply_markup=markup, parse_mode=ParseMode.HTML,
            disable_web_page_preview=bool(post.title or post.description),
        )

    return message.message_id, image, image_id


@with_session
def send_new_posts(context: CallbackContext, session: Session):
    for chat in session.query(Chat).all():
        with suppress(StopIteration):
            iterable, value = get_new_posts(session, chat), None
            while True:
                post, channel, adapter = iterable.send(value)
                value = send_post(post, channel, adapter, chat, context.bot)


@with_session
def remove_old_posts(context: CallbackContext, session: Session):
    outdated = session.query(ChatPost).where(ChatPost.state == ChatPostState.Posted).where(
        ChatPost.post.has(Post.created < datetime.utcnow() - timedelta(days=1))
    )

    for chat_post in outdated.all():
        delete_message(context.bot, chat_post.chat.identifier, chat_post.message_id)

        chat_post.state = ChatPostState.Deleted
        session.flush()


@no_context
def fallback(update: Update):
    update.message.reply_text('Unknown command', quote=True)


def on_error(update, context: CallbackContext):
    # raise context.error
    logger.warning('Update "%s" caused error %s: %s', update, type(context.error).__name__, context.error)


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
    job_queue.run_repeating(with_session(
        lambda context, session: update_base(session)), interval=crawler_interval, first=0)

    return updater
