import asyncio
import logging
import secrets

from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

import cradlex.handlers  # noqa: F401
from cradlex import config
from cradlex.bot import bot
from cradlex.bot import dp


async def on_startup(webhook_path=None, *args):
    """Prepare bot before starting.

    Set webhook and run background tasks.
    """
    await bot.delete_webhook()
    if webhook_path is not None:
        await bot.set_webhook("https://" + config.SERVER_HOST + webhook_path)


logging.basicConfig(level=config.LOGGER_LEVEL)
dp.middleware.setup(LoggingMiddleware())

if config.SET_WEBHOOK:
    url_token = secrets.token_urlsafe()
    webhook_path = config.WEBHOOK_PATH + "/" + url_token

    executor.start_webhook(
        dispatcher=dp,
        webhook_path=webhook_path,
        on_startup=lambda *args: on_startup(webhook_path, *args),
        host=config.INTERNAL_HOST,
        port=config.SERVER_PORT,
    )
else:
    executor.start_polling(dispatcher=dp, skip_updates=config.SKIP_UPDATES)
print()  # noqa: T001  Executor stopped with ^C

# Stop all background tasks
loop = asyncio.get_event_loop()
for task in asyncio.all_tasks(loop):
    task.cancel()
    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass
