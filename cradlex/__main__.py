import asyncio
import datetime
import functools
import logging
import secrets

import sqlalchemy as sa
from aiogram import types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

import cradlex.handlers  # noqa: F401
from cradlex import callback_data
from cradlex import config
from cradlex import database
from cradlex import models
from cradlex.bot import bot
from cradlex.bot import dp
from cradlex.i18n import _
from cradlex.models import Base


async def task_loop():
    timeliness_markup = types.InlineKeyboardMarkup(row_width=1)
    timeliness_markup.add(
        types.InlineKeyboardButton(
            _("on_time"),
            callback_data=callback_data.task_timeliness.new(
                timeliness=models.TaskTimeliness.on_time.name
            ),
        ),
        types.InlineKeyboardButton(
            _("late"),
            callback_data=callback_data.task_timeliness.new(
                timeliness=models.TaskTimeliness.late.name
            ),
        ),
        types.InlineKeyboardButton(
            _("very_late"),
            callback_data=callback_data.task_timeliness.new(
                timeliness=models.TaskTimeliness.very_late.name
            ),
        ),
    )
    start_markup = types.InlineKeyboardMarkup(row_width=1)
    start_markup.add(
        types.InlineKeyboardButton(_("task_done"), callback_data="task_done"),
    )
    while True:
        max_time = sa.func.current_timestamp() + datetime.timedelta(minutes=30)
        async with database.sessionmaker() as session:
            async with session.begin():
                timeliness_ids_cursor = await session.execute(
                    sa.update(models.Task)
                    .where(
                        models.Task.time <= max_time,
                        models.Task.worker_id != None,  # noqa: E711
                        models.Task.timeliness == None,  # noqa: E711
                    )
                    .values(timeliness=models.TaskTimeliness.unknown)
                    .returning(models.Task.worker_id)
                    .execution_options(synchronize_session=False)
                )
                start_ids_cursor = await session.execute(
                    sa.update(models.Task)
                    .where(
                        models.Task.time <= sa.func.current_timestamp(),
                        models.Task.worker_id != None,  # noqa: E711
                        models.Task.timeliness != None,  # noqa: E711
                        sa.not_(models.Task.sent),
                    )
                    .values(sent=True)
                    .returning(models.Task.worker_id)
                    .execution_options(synchronize_session=False)
                )
                timeliness_ids = timeliness_ids_cursor.scalars().all()
                start_ids = start_ids_cursor.scalars().all()
        for timeliness_id in timeliness_ids:
            try:
                await bot.send_message(
                    timeliness_id, _("verify_task"), reply_markup=timeliness_markup
                )
            except Exception as error:
                logging.getLogger(__name__).error(
                    f"Error verifying task of worker {timeliness_id}: {error}"
                )
            else:
                await asyncio.sleep(0.05)
        for start_id in start_ids:
            try:
                await bot.send_message(
                    start_id, _("task_started"), reply_markup=start_markup
                )
            except Exception as error:
                logging.getLogger(__name__).error(
                    f"Error starting task of worker {timeliness_id}: {error}"
                )
            else:
                await asyncio.sleep(0.05)
        await asyncio.sleep(60)


async def on_startup(*args, webhook_path=None):
    """Prepare bot before starting.

    Set webhook and run background tasks.
    """
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await bot.delete_webhook()
    if webhook_path is not None:
        await bot.set_webhook("https://" + config.SERVER_HOST + webhook_path)
    asyncio.create_task(task_loop())


logging.basicConfig(level=config.LOGGER_LEVEL)
dp.middleware.setup(LoggingMiddleware())

if config.SET_WEBHOOK:
    url_token = secrets.token_urlsafe()
    webhook_path = config.WEBHOOK_PATH + "/" + url_token

    executor.start_webhook(
        dispatcher=dp,
        webhook_path=webhook_path,
        on_startup=functools.partial(on_startup, webhook_path=webhook_path),
        host=config.INTERNAL_HOST,
        port=config.SERVER_PORT,
    )
else:
    executor.start_polling(
        dispatcher=dp, on_startup=on_startup, skip_updates=config.SKIP_UPDATES
    )
print()  # noqa: T001  Executor stopped with ^C

# Stop all background tasks
loop = asyncio.get_event_loop()
for task in asyncio.all_tasks(loop):
    task.cancel()
    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass
