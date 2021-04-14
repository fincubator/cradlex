from aiogram import Bot
from aiogram import Dispatcher

from cradlex import config
from cradlex import database
from cradlex.i18n import i18n
from cradlex.user import user_middleware

with open(config.TOKEN_FILENAME, "r") as token_file:
    bot = Bot(token_file.read().strip())

dp = Dispatcher(bot)
dp.storage = database.PostgreStorage()
dp.middleware.setup(user_middleware)
dp.middleware.setup(i18n)
