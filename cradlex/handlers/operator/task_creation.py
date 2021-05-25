import asyncio
import datetime
import re
import typing

import pytz
import sqlalchemy as sa
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import any_state
from aiogram.dispatcher.filters.state import State

from cradlex import callback_data
from cradlex import database
from cradlex import models
from cradlex import utils
from cradlex.bot import dp
from cradlex.filters import OperatorFilter
from cradlex.i18n import _
from cradlex.states import TaskCreation


step_handlers = {}


def step_handler(state: State):
    def decorator(callback):
        step_handlers[state._state] = callback
        return callback

    return decorator


@dp.message_handler(OperatorFilter(), commands=["create_task"], state=any_state)
async def create_task(message: types.Message, state: FSMContext):
    keyboard_markup = await utils.get_task_types_keyboard()
    if not keyboard_markup.keyboard:
        return await message.answer(_("no_task_types"))
    await TaskCreation.payment.set()
    await message.answer(_("ask_task_payment"))


@step_handler(TaskCreation.payment)
async def payment_step(message: types.Message, state: FSMContext) -> bool:
    try:
        payment = int(message.text)
    except ValueError:
        await message.answer(_("not_integer_error"))
        return False
    if payment <= 0:
        await message.answer(_("not_positive_error"))
        return False
    await state.update_data(payment=payment)
    return True


@dp.message_handler(state=TaskCreation.payment)
async def set_task_payment(message: types.Message, state: FSMContext):
    if await payment_step(message, state):
        await TaskCreation.location.set()
        await message.answer(_("ask_task_location"))


@step_handler(TaskCreation.location)
async def location_step(message: types.Message, state: FSMContext) -> bool:
    await state.update_data(location=message.text)
    return True


@dp.message_handler(state=TaskCreation.location)
async def set_task_location(message: types.Message, state: FSMContext):
    if await location_step(message, state):
        await TaskCreation.time.set()
        await message.answer(_("ask_task_time"))


@step_handler(TaskCreation.time)
async def time_step(message: types.Message, state: FSMContext) -> bool:
    time_match = re.search(r"(?P<hour>\d\d?):(?P<minute>\d\d?)", message.text)
    if not time_match:
        await message.answer(_("no_time_error"))
        return False
    time_dict = time_match.groupdict()
    for key, value in time_dict.items():
        time_dict[key] = int(value)
    date_match = re.search(
        r"(?P<day>\d\d?)[./-](?P<month>\d\d?)",
        message.text,
    )
    date_dict: typing.Optional[typing.Dict] = None
    if date_match:
        date_dict = date_match.groupdict()
        for key, value in date_dict.items():
            date_dict[key] = int(value)
    tzinfo = pytz.timezone("Europe/Moscow")
    now = datetime.datetime.now(tzinfo)
    try:
        if date_dict:
            time = tzinfo.localize(
                datetime.datetime(
                    now.year,
                    date_dict["month"],
                    date_dict["day"],
                    time_dict["hour"],
                    time_dict["minute"],
                )
            )
            if time <= now:
                time.replace(year=now.year + 1)
        else:
            time = tzinfo.localize(
                datetime.datetime(
                    now.year,
                    now.month,
                    now.day,
                    time_dict["hour"],
                    time_dict["minute"],
                )
            )
            if time <= now:
                time += datetime.timedelta(days=1)
    except ValueError:
        await message.answer(_("invalid_date_error"))
        return False
    await state.update_data(time=time.isoformat())
    return True


@dp.message_handler(state=TaskCreation.time)
async def set_task_time(message: types.Message, state: FSMContext):
    if await time_step(message, state):
        await TaskCreation.contact.set()
        await message.answer(_("ask_task_contact"))


@step_handler(TaskCreation.contact)
async def contact_step(message: types.Message, state: FSMContext) -> bool:
    await state.update_data(contact=message.text)
    return True


@dp.message_handler(state=TaskCreation.contact)
async def set_task_contact(message: types.Message, state: FSMContext):
    if not await contact_step(message, state):
        return
    keyboard_markup = await utils.get_task_types_keyboard()
    if not keyboard_markup.keyboard:
        await state.finish()
        return await message.answer(_("no_task_types"))
    await TaskCreation.task_type.set()
    await message.answer(_("ask_task_type"), reply_markup=keyboard_markup)


@step_handler(TaskCreation.task_type)
async def task_type_step(message: types.Message, state: FSMContext) -> bool:
    task_type_result = utils.parse_task_type(message.text)
    if not task_type_result:
        await message.answer(_("task_type_invalid_error"))
        return False
    name, difficulty = task_type_result
    async with database.sessionmaker() as session:
        async with session.begin():
            task_type_cursor = await session.execute(
                sa.select(models.TaskType).where(
                    models.TaskType.name == name,
                    models.TaskType.difficulty == difficulty,
                )
            )
        try:
            task_type = task_type_cursor.one()[0]
        except sa.exc.NoResultFound:
            await message.answer(_("task_type_not_found_error"))
            return False
    await state.update_data(type_id=task_type.id)
    return True


@dp.message_handler(state=TaskCreation.task_type)
async def set_task_type(message: types.Message, state: FSMContext):
    if await task_type_step(message, state):
        await check_task(message, state)


async def check_task(
    update: typing.Union[types.Message, types.CallbackQuery], state: FSMContext
):
    keyboard_markup = types.InlineKeyboardMarkup()
    keyboard_markup.row(
        types.InlineKeyboardButton(_("edit_task"), callback_data="edit_task"),
        types.InlineKeyboardButton(_("broadcast_task"), callback_data="broadcast_task"),
    )
    await TaskCreation.check_task.set()
    task = await utils.task_message(await state.get_data())
    text = _("check_task") + "\n" + task
    if isinstance(update, types.Message):
        await update.answer(text, reply_markup=keyboard_markup)
    elif isinstance(update, types.CallbackQuery):
        await update.message.edit_text(text, reply_markup=keyboard_markup)


@dp.callback_query_handler(
    lambda call: call.data == "cancel_edit_task",
    state=TaskCreation.edit_task,
)
async def cancel_edit_task(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await check_task(call, state)


@dp.callback_query_handler(
    lambda call: call.data == "edit_task",
    state=TaskCreation.check_task,
)
async def edit_task_start(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lines = await utils.task_message_lines(data)
    buttons = []
    for i, key in enumerate(lines.keys()):
        buttons.append(
            types.InlineKeyboardButton(
                str(i + 1), callback_data=callback_data.edit_task_step.new(step=key)
            )
        )
    keyboard_markup = types.InlineKeyboardMarkup()
    keyboard_markup.row(*buttons)
    keyboard_markup.row(
        types.InlineKeyboardButton(
            _("cancel_edit_task"), callback_data="cancel_edit_task"
        )
    )
    await TaskCreation.edit_task.set()
    await call.answer()
    await call.message.edit_text(
        _("task_editing") + "\n" + utils.message_from_lines(lines, numbered=True),
        reply_markup=keyboard_markup,
    )


@dp.callback_query_handler(
    callback_data.edit_task_step.filter(),
    state=TaskCreation.edit_task,
)
async def edit_task_step(
    call: types.CallbackQuery,
    callback_data: typing.Mapping[str, str],
    state: FSMContext,
):
    step = callback_data["step"]
    if step == TaskCreation.payment._state:
        answer = _("ask_new_payment")
    elif step == TaskCreation.location._state:
        answer = _("ask_new_location")
    elif step == TaskCreation.time._state:
        answer = _("ask_new_time")
    elif step == TaskCreation.contact._state:
        answer = _("ask_new_contact")
    elif step == TaskCreation.task_type._state:
        answer = _("ask_new_type")
    else:
        await call.answer(_("unknown_step"))
        return await check_task(call, state)
    await state.update_data(edit_step=step)
    await call.answer()
    await call.message.edit_text(answer)


@dp.message_handler(state=TaskCreation.edit_task)
async def edit_task_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if await step_handlers[data["edit_step"]](message, state):
        await check_task(message, state)


@dp.callback_query_handler(
    lambda call: call.data == "broadcast_task",
    state=TaskCreation.check_task,
)
async def broadcast_task(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        task = models.Task(
            location=data["location"],
            time=datetime.datetime.fromisoformat(data["time"]),
            contact=data["contact"],
            type_id=data["type_id"],
            payment=data["payment"],
        )
    async with database.sessionmaker() as session:
        async with session.begin():
            session.add(task)
    asyncio.create_task(utils.broadcast_task(task))
    await state.finish()
    await call.answer()
    await call.message.answer(_("task_broadcasted"))
