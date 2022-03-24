from contextlib import suppress

from telegram import TelegramError, Bot, InputMediaPhoto


def delete_message(bot: Bot, chat_id, message_id):
    with suppress(TelegramError):
        bot.delete_message(chat_id, message_id)
        return

    message = "<Deleted>"
    with suppress(TelegramError):
        bot.edit_message_text(message, chat_id, message_id)
    with suppress(TelegramError):
        bot.edit_message_media(
            chat_id, message_id,
            media=InputMediaPhoto('https://raster.shields.io/badge/-deleted-red')
        )
        return
    with suppress(TelegramError):
        bot.edit_message_caption(chat_id, message_id, caption=message)
