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
            vacant = models.Task.worker_id == None  # noqa: E711
            unexpired = models.Task.time > sa.func.current_timestamp()
            task_properties_cursor = await session.execute(
                sa.select(
                    vacant.label("vacant"), unexpired.label("unexpired")  # type: ignore
                )
                .where(models.Task.id == callback_data["task_id"])
                .execution_options(synchronize_session=False)
            )
            task_properties = task_properties_cursor.one_or_none()
            if not task_properties:
                error = _("task_not_exists_error")
            elif not task_properties.vacant:
                error = _("task_already_taken_error")
            elif not task_properties.unexpired:
                error = _("task_expired_error")
            else:
                await session.execute(
                    sa.update(models.Task)
                    .values(worker_id=call.from_user.id)
                    .where(models.Task.id == callback_data["task_id"])
                )
                await call.answer(_("task_taken"), show_alert=True)
                await call.message.delete_reply_markup()
                messages_to_delete = await session.execute(
                    sa.delete(models.TaskMessage)
                    .where(
                        models.TaskMessage.task_id == callback_data["task_id"],
                        models.TaskMessage.worker_id != call.from_user.id,
                    )
                    .returning(models.TaskMessage.worker_id, models.TaskMessage.id)
                )
                asyncio.create_task(
                    utils.delete_task_messages(messages_to_delete.all())
                )
                return
        await call.answer(error, show_alert=True)
        await call.message.delete()


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


@dp.callback_query_handler(lambda call: call.data == "task_done")
async def task_done(call: types.CallbackQuery):
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
