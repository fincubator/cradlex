import logging

from aiogram import types
from aiogram.dispatcher.filters import CommandHelp
from aiogram.dispatcher.filters import CommandStart
from aiogram.utils.exceptions import MessageNotModified

from cradlex.bot import dp


@dp.message_handler(CommandStart())
@dp.message_handler(CommandHelp())
async def start_command(message: types.Message):
    """Handle /start."""
    await message.answer(
        "Hello, I'm Cradlex. I'm an ERP telegram bot for small builder groups."
    )


@dp.errors_handler()
async def errors_handler(update: types.Update, exception: Exception):
    """Handle exceptions when calling handlers."""
    if isinstance(exception, MessageNotModified):
        return True

    logging.getLogger(__name__).error(
        "Error handling request {}".format(update.update_id), exc_info=True
    )
    return True
