import asyncio
import typing

import sqlalchemy as sa
from aiogram import types
from aiogram.dispatcher import FSMContext

from cradlex import callback_data
from cradlex import config
from cradlex import database
from cradlex import models
from cradlex import utils
from cradlex.bot import bot
from cradlex.bot import dp
from cradlex.i18n import _
from cradlex.states import task_photo


@dp.callback_query_handler(callback_data.take_task.filter())
async def take_task(
    call: types.CallbackQuery,
    callback_data: typing.Mapping[str, str],
):
    async with database.sessionmaker() as session:
        async with session.begin():
            result = await session.execute(
                sa.update(models.Task)
                .values(worker_id=call.from_user.id)
                .where(
                    models.Task.id == callback_data["task_id"],
                    models.Task.worker_id is None,
                )
            )
        if result.one_or_none():
            await call.answer("Вы взяли задание.", show_alert=True)
            await call.message.delete_reply_markup()
            async with session.begin():
                messages_to_delete = await session.execute(
                    sa.delete(models.TaskMessage)
                    .where(
                        models.TaskMessage.task_id == callback_data["task_id"],
                        models.TaskMessage.worker_id != call.from_user.id,
                    )
                    .returning(models.TaskMessage.worker_id, models.TaskMessage.id)
                )
            asyncio.create_task(utils.delete_task_messages(messages_to_delete.all()))
        else:
            await call.answer("Вы уже не можете взять это задание.")
            await call.message.delete()
            return


@dp.callback_query_handler(callback_data.task_timeliness.filter())
async def verify_task(
    call: types.CallbackQuery,
    callback_data: typing.Mapping[str, str],
):
    async with database.sessionmaker() as session:
        async with session.begin():
            await session.execute(
                sa.update(models.Task)
                .values(timeliness=callback_data["timeliness"])
                .where(models.Task.worker_id == call.from_user.id)
            )
    await call.answer("task_verified")
    await call.message.delete_reply_markup()


@dp.callback_query_handler(lambda call: call.data == "finish_task")
async def finish_task(call: types.CallbackQuery):
    await task_photo.set()
    await call.answer()
    await call.message.answer(_("make_photo"))


@dp.message_handler(content_types=types.ContentType.PHOTO, state=task_photo)
async def send_photo(message: types.Message, state: FSMContext):
    async with database.sessionmaker() as session:
        async with session.begin():
            task_id = await session.scalar(
                sa.select(models.Task.id).where(
                    models.Task.worker_id == message.from_user.id
                )
            )
    keyboard_markup = types.InlineKeyboardMarkup(row_width=1)
    keyboard_markup.add(
        types.InlineKeyboardButton(
            _("bad_job"),
            callback_data=callback_data.review_task.new(
                task_id=task_id, review="bad_job"
            ),
        ),
        types.InlineKeyboardButton(
            _("bad_photo"),
            callback_data=callback_data.review_task.new(
                task_id=task_id, review="bad_photo"
            ),
        ),
        types.InlineKeyboardButton(
            _("good_job"),
            callback_data=callback_data.review_task.new(
                task_id=task_id, review="good_job"
            ),
        ),
    )
    await message.forward(chat_id=config.OPERATOR_ID)
    await bot.send_message(
        config.OPERATOR_ID, _("review_job"), reply_markup=keyboard_markup
    )
    await message.answer(_("photo_forwarded"))
    await state.finish()
