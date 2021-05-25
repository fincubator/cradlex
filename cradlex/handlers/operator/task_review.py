import typing

import sqlalchemy as sa
from aiogram import types

from cradlex import callback_data
from cradlex import database
from cradlex import models
from cradlex import states
from cradlex import utils
from cradlex.bot import bot
from cradlex.bot import dp
from cradlex.filters import OperatorFilter
from cradlex.i18n import _


@dp.callback_query_handler(OperatorFilter(), callback_data.review_task.filter())
async def review_task(
    call: types.CallbackQuery, callback_data: typing.Mapping[str, str]
):
    async with database.sessionmaker() as session:
        async with session.begin():
            worker_cursor = await session.execute(
                sa.select(models.Worker)
                .join(models.Task)
                .where(models.Task.id == callback_data["task_id"])
            )
            worker = worker_cursor.one()
    await call.answer()
    review = callback_data["review"]
    redo = True
    if review == "bad_job":
        operator_answer = _("task_reviewed")
        worker_answer = _("redo_job")
    elif review == "bad_photo":
        operator_answer = _("task_reviewed")
        worker_answer = _("redo_photo")
    elif review == "good_job":
        operator_answer = _("pay_worker") + "\n" + await utils.worker_message(worker)
        worker_answer = _("task_successful")
        redo = False
    else:
        return
    if redo:
        await dp.storage.set_state(user=worker.id, state=states.task_photo.state)
    await call.message.answer(call.from_user.id, operator_answer)
    await bot.send_message(worker.id, worker_answer)
