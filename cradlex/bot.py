from aiogram import Bot
from aiogram import Dispatcher

from cradlex import config

with open(config.TOKEN_FILENAME, "r") as token_file:
    bot = Bot(token_file.read().strip())
dp = Dispatcher(bot)
