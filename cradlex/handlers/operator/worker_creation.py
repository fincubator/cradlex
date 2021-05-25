import typing

import phonenumbers
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
from cradlex.states import WorkerCreation


step_handlers = {}


def step_handler(state: State):
    def decorator(callback):
        step_handlers[state._state] = callback
        return callback

    return decorator


@dp.message_handler(OperatorFilter(), commands=["enter_worker"], state=any_state)
async def create_worker(message: types.Message, state: FSMContext):
    await WorkerCreation.name.set()
    await message.answer(_("ask_worker_name"))


@step_handler(WorkerCreation.name)
async def name_step(message: types.Message, state: FSMContext) -> bool:
    name = " ".join(map(lambda word: word.capitalize(), message.text.split()))
    await state.update_data(name=name)
    return True


@dp.message_handler(state=WorkerCreation.name)
async def set_worker_name(message: types.Message, state: FSMContext):
    if await name_step(message, state):
        await WorkerCreation.phone.set()
        await message.answer(_("ask_worker_phone"))


@step_handler(WorkerCreation.phone)
async def phone_step(message: types.Message, state: FSMContext) -> bool:
    try:
        number = phonenumbers.parse(message.text, region="RU")
    except phonenumbers.NumberParseException:
        await message.answer(_("phone_parse_error"))
        return False
    phone = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
    await state.update_data(phone=phone)
    return True


def skill_keyboard() -> types.ReplyKeyboardMarkup:
    buttons = utils.skill_levels()
    keyboard_markup = types.ReplyKeyboardMarkup(
        row_width=1, one_time_keyboard=True, resize_keyboard=True
    )
    keyboard_markup.add(*buttons)
    return keyboard_markup


@dp.message_handler(state=WorkerCreation.phone)
async def set_worker_phone(message: types.Message, state: FSMContext):
    if not await phone_step(message, state):
        return
    await WorkerCreation.skill.set()
    await message.answer(_("ask_worker_skill"), reply_markup=skill_keyboard())


@step_handler(WorkerCreation.skill)
async def skill_step(message: types.Message, state: FSMContext) -> bool:
    try:
        skill = models.WORKER_SKILL[len(message.text.split()[0]) - 1]
    except IndexError:
        await message.answer(_("skill_invalid_error"))
        return False
    await state.update_data(skill=skill)
    return True


@dp.message_handler(state=WorkerCreation.skill)
async def set_worker_skill(message: types.Message, state: FSMContext):
    if await skill_step(message, state):
        await check_worker(message, state)


async def check_worker(
    update: typing.Union[types.Message, types.CallbackQuery], state: FSMContext
):
    keyboard_markup = types.InlineKeyboardMarkup()
    keyboard_markup.row(
        types.InlineKeyboardButton(_("edit_worker"), callback_data="edit_worker"),
        types.InlineKeyboardButton(_("save_worker"), callback_data="save_worker"),
    )
    await WorkerCreation.check_worker.set()
    worker = await utils.worker_message(await state.get_data())
    text = _("check_worker") + "\n" + worker
    if isinstance(update, types.Message):
        await update.answer(text, reply_markup=keyboard_markup)
    elif isinstance(update, types.CallbackQuery):
        await update.message.edit_text(text, reply_markup=keyboard_markup)


@dp.callback_query_handler(
    lambda call: call.data == "cancel_edit_worker",
    state=WorkerCreation.edit_worker,
)
async def cancel_edit_worker(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await check_worker(call, state)


@dp.callback_query_handler(
    lambda call: call.data == "edit_worker",
    state=WorkerCreation.check_worker,
)
async def edit_worker_start(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lines = await utils.worker_message_lines(data)
    buttons = []
    for i, key in enumerate(lines.keys()):
        buttons.append(
            types.InlineKeyboardButton(
                str(i + 1),
                callback_data=callback_data.edit_worker_step.new(step=key),
            )
        )
    keyboard_markup = types.InlineKeyboardMarkup()
    keyboard_markup.row(*buttons)
    keyboard_markup.row(
        types.InlineKeyboardButton(
            _("cancel_edit_worker"), callback_data="cancel_edit_worker"
        )
    )
    await WorkerCreation.edit_worker.set()
    await call.answer()
    await call.message.edit_text(
        _("worker_editing") + "\n" + utils.message_from_lines(lines, numbered=True),
        reply_markup=keyboard_markup,
    )


@dp.callback_query_handler(
    callback_data.edit_worker_step.filter(),
    state=WorkerCreation.edit_worker,
)
async def edit_worker_step(
    call: types.CallbackQuery,
    callback_data: typing.Mapping[str, str],
    state: FSMContext,
):
    step = callback_data["step"]
    reply_keyboard = None
    if step == WorkerCreation.name._state:
        answer = _("ask_new_name")
    elif step == WorkerCreation.phone._state:
        answer = _("ask_new_phone")
    elif step == WorkerCreation.skill._state:
        answer = _("ask_new_skill")
        reply_keyboard = skill_keyboard()
    else:
        await call.answer(_("unknown_step"))
        return await check_worker(call, state)
    await state.update_data(edit_step=step)
    await call.answer()
    if reply_keyboard is None:
        await call.message.edit_text(answer)
    else:
        await call.message.delete()
        await call.message.answer(answer, reply_markup=reply_keyboard)


@dp.message_handler(state=WorkerCreation.edit_worker)
async def edit_worker_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if await step_handlers[data["edit_step"]](message, state):
        await check_worker(message, state)


@dp.callback_query_handler(
    lambda call: call.data == "save_worker",
    state=WorkerCreation.check_worker,
)
async def save_worker(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        worker = models.Worker(
            name=data["name"],
            phone=data["phone"],
            skill=data["skill"],
        )
    async with database.sessionmaker() as session:
        async with session.begin():
            session.add(worker)
    await state.finish()
    await call.answer()
    await call.message.answer(_("worker_saved"))
