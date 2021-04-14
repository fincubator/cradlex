import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.filters.state import any_state
from aiogram.utils.exceptions import MessageNotModified

from cradlex.bot import dp
from cradlex.i18n import _


@dp.message_handler(CommandStart(), state=any_state)
async def start_command(message: types.Message, state: FSMContext):
    """Handle /start."""
    await state.finish()
    await message.answer(_("start_message"), reply_markup=types.ReplyKeyboardRemove())


@dp.errors_handler()
async def errors_handler(update: types.Update, exception: Exception):
    """Handle exceptions when calling handlers."""
    if not isinstance(exception, MessageNotModified):
        logging.getLogger(__name__).error(
            "Error handling request {}".format(update.update_id), exc_info=True
        )
    return True
