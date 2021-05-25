from aiogram import types
from aiogram.dispatcher.filters.filters import Filter

from cradlex import config


class OperatorFilter(Filter):
    async def check(self, obj: types.base.TelegramObject) -> bool:
        if isinstance(obj, types.Message):
            return obj.from_user.id == obj.chat.id == config.OPERATOR_ID
        elif isinstance(obj, types.CallbackQuery):
            return obj.from_user.id == obj.message.chat.id == config.OPERATOR_ID
        else:
            return False
