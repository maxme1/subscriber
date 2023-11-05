import logging
from contextlib import suppress
from urllib.parse import quote_plus

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from ..models import Identifier, Post
from ..utils import URL_PATTERN, drop_prefix, storage_resolve
from .interface import Destination

logger = logging.getLogger(__name__)


class Telegram(Destination):
    def __init__(self, token: str):
        app = Application.builder().token(token).build()
        app.add_error_handler(on_error)

        app.add_handler(CommandHandler('start', start))
        app.add_handler(MessageHandler(filters.Regex(URL_PATTERN), self._link))
        # list sources
        app.add_handler(CommandHandler('list', self._list))
        # delete sources
        app.add_handler(CommandHandler('delete', self._delete))
        app.add_handler(CallbackQueryHandler(self._delete_callback, pattern='DELETE'))
        # message commands
        app.add_handler(CallbackQueryHandler(self._dismiss_callback, pattern='DISMISS'))
        app.add_handler(CallbackQueryHandler(self._keep, pattern='KEEP'))
        # didn't understand the user
        app.add_handler(MessageHandler(filters.ALL, fallback))

        self.app = app
        self.bot: Bot = app.bot

    # events

    async def start(self):
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

    async def stop(self):
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()

    # TODO: add throttling
    async def notify(self, chat_id: Identifier, post: Post) -> Identifier:
        description = post.description
        if len(description) > 3800:
            description = description[:3800] + '...'
        text = f'{post.title}\n{description}\n{post.url}'.strip()
        if '<' in text:
            text = quote_plus(text)
        parse_mode = ParseMode.MARKDOWN_V2
        image = post.image

        markup = InlineKeyboardMarkup.from_row([
            InlineKeyboardButton('Keep', callback_data='KEEP'),
            InlineKeyboardButton('Dismiss', callback_data='DISMISS'),
        ])

        if image is None:
            message = await self.bot.send_message(
                chat_id, text, reply_markup=markup, parse_mode=parse_mode,
                disable_web_page_preview=bool(post.title or description),
            )

        elif image.telegram is None:
            # TODO: need another adapter?
            with open(storage_resolve(image.internal), 'rb') as img:
                message = await self.bot.send_photo(
                    chat_id, img, parse_mode=parse_mode, caption=text, reply_markup=markup
                )
                await self.save_image(image.internal, message.photo[0].file_id)

        else:
            message = await self.bot.send_photo(
                chat_id, image.telegram, parse_mode=parse_mode, caption=text, reply_markup=markup
            )

        return str(message.message_id)

    async def remove(self, chat_id: Identifier, message_id: Identifier):
        message_id = int(message_id)
        with suppress(TelegramError):
            await self.bot.delete_message(chat_id, message_id)
            return

        message = '<Deleted>'
        with suppress(TelegramError):
            await self.bot.edit_message_text(message, chat_id, message_id)
            return
        with suppress(TelegramError):
            await self.bot.edit_message_media(
                # TODO: upload once
                InputMediaPhoto('https://raster.shields.io/badge/-deleted-red'),
                chat_id, message_id,
            )
            return
        with suppress(TelegramError):
            await self.bot.edit_message_caption(chat_id, message_id, caption=message)
            return

    # callbacks

    async def _keep(self, update: Update, context: CallbackContext):
        query = update.callback_query
        message = query.message
        await self.keep(str(message.message_id))
        await message.edit_reply_markup(InlineKeyboardMarkup.from_button(
            InlineKeyboardButton('Dismiss', callback_data='DISMISS')
        ))

    async def _link(self, update: Update, context: CallbackContext):
        message = update.message
        url = message.text.strip()

        await message.reply_text(
            await self.subscribe(str(message.chat.id), url),
            quote=True,
        )

    async def _list(self, update: Update, context: CallbackContext):
        message = update.message
        channels = await self.list(str(message.chat.id))
        channels = '\n'.join(c.name for c in channels)
        if not channels:
            channels = 'You have no subscriptions'
        await message.reply_text(channels)

    async def _delete(self, update: Update, context: CallbackContext):
        message = update.message
        text, markup = make_keyboard(await self.list(str(message.chat_id)))
        await message.reply_text(text, reply_markup=markup)

    async def _delete_callback(self, update: Update, context: CallbackContext):
        query = update.callback_query
        message = query.message
        chat_id = str(message.chat.id)
        await self.unsubscribe(chat_id, drop_prefix(query.data, 'DELETE:'))

        text, markup = make_keyboard(await self.list(chat_id))
        await message.edit_reply_markup(markup)

    async def _dismiss_callback(self, update: Update, context: CallbackContext):
        message = update.callback_query.message
        await self.remove(str(message.chat_id), str(message.message_id))


async def start(update: Update, context: CallbackContext):
    await context.bot.send_message(
        update.message.chat.id,
        # language=Markdown
        r'''
Hi\! I can notify you about
 • new videos in [YouTube](https://www.youtube.com) channels
 • new posts in [Twitter](https://twitter.com/) feeds
 • new concerts for artists and bands from [SongKick](https://songkick.com/) 
 • new posts from [VK](https://vk.com/) public channels
 • new [Kaggle](https://www.kaggle.com/) competitions
 • new [GrandChallenge](https://grand-challenge.org/) competitions

Just send me a link and let's get started\!''',
        parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True,
    )


async def fallback(update: Update, context: CallbackContext):
    await update.message.reply_text('Unknown command', quote=True)


async def on_error(update, context: CallbackContext):
    # raise context.error
    logger.warning('Update "%s" caused error %s: %s', update, type(context.error).__name__, context.error)


def make_keyboard(channels):
    buttons = [InlineKeyboardButton(c.name, callback_data=f'DELETE:{c.pk}') for c in channels]
    if not buttons:
        return 'You have no subscriptions', None

    return 'Chose a channel to delete', InlineKeyboardMarkup([buttons[i:i + 2] for i in range(0, len(buttons), 2)])
