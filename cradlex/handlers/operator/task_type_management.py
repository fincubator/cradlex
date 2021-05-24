import sqlalchemy as sa
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import any_state
from aiogram.utils.emoji import emojize

from cradlex import database
from cradlex import models
from cradlex import utils
from cradlex.bot import dp
from cradlex.i18n import _
from cradlex.states import type_deletion
from cradlex.states import TypeCreation


@dp.message_handler(commands=["create_type"], state=any_state)
async def start_type_creation(message: types.Message, state: FSMContext):
    await TypeCreation.name.set()
    await message.answer(_("ask_type_to_create"))


@dp.message_handler(state=TypeCreation.name)
async def set_type_name(message: types.Message, state: FSMContext):
    star = emojize(":star:")
    diffs = len(models.TASK_DIFFICULTY) + 1
    keyboard_markup = types.ReplyKeyboardMarkup(
        row_width=diffs, one_time_keyboard=True, resize_keyboard=True
    )
    keyboard_markup.add(*(star * i for i in range(diffs)))
    await state.update_data(name=message.text.lower().capitalize())
    await TypeCreation.difficulty.set()
    await message.answer(_("ask_type_difficulty"), reply_markup=keyboard_markup)


@dp.message_handler(state=TypeCreation.difficulty)
async def set_type_difficulty(message: types.Message, state: FSMContext):
    difficulty_index = len(message.text)
    if not 1 <= difficulty_index <= len(models.TASK_DIFFICULTY):
        return await message.answer(_("unknown_difficulty_error"))
    difficulty = models.TASK_DIFFICULTY[difficulty_index - 1]
    async with state.proxy() as data:
        task_type = models.TaskType(name=data["name"], difficulty=difficulty)
    async with database.sessionmaker() as session:
        async with session.begin():
            session.add(task_type)
    await state.finish()
    await message.answer(
        _("task_type_created"), reply_markup=types.ReplyKeyboardRemove()
    )


@dp.message_handler(commands=["delete_type"], state=any_state)
async def start_type_deletion(message: types.Message, state: FSMContext):
    keyboard_markup = await utils.get_task_types_keyboard()
    if not keyboard_markup.keyboard:
        return await message.answer(_("no_types_to_delete"))
    await type_deletion.set()
    await message.answer(_("ask_type_to_delete"), reply_markup=keyboard_markup)


@dp.message_handler(state=type_deletion)
async def finish_type_deletion(message: types.Message, state: FSMContext):
    task_type_result = utils.parse_task_type(message.text)
    if not task_type_result:
        await message.answer(_("task_type_invalid_error"))
        return False
    name, difficulty = task_type_result
    async with database.sessionmaker() as session:
        async with session.begin():
            task_type_cursor = await session.execute(
                sa.delete(models.TaskType)
                .where(
                    models.TaskType.name == name,
                    models.TaskType.difficulty == difficulty,
                )
                .returning(models.TaskType.id)
            )
        try:
            task_type_cursor.one()
        except sa.exc.NoResultFound:
            return await message.answer(_("task_type_not_found_error"))
    await state.finish()
    await message.answer(
        _("task_type_deleted"), reply_markup=types.ReplyKeyboardRemove()
    )
