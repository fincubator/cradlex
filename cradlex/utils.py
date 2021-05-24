import asyncio
import logging
import re
import typing
from datetime import datetime

import phonenumbers
import sqlalchemy as sa
from aiogram import types
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.emoji import emojize

from cradlex import database
from cradlex import models
from cradlex import states
from cradlex.bot import bot
from cradlex.i18n import _


DATE_FORMAT = "%d.%m.%Y %H:%M"

take_task_cb = CallbackData("take_task", "task_id")


def message_from_lines(lines: typing.Mapping[str, str], numbered: bool = False) -> str:
    if numbered:
        line_values = [f"{i + 1}. {line}" for i, line in enumerate(lines.values())]
    else:
        line_values = list(lines.values())
    return "\n".join(line_values)


def task_string(task_type: models.TaskType) -> str:
    name = task_type.name
    difficulty = models.TASK_DIFFICULTY.index(task_type.difficulty) + 1
    star = emojize(":star:")
    return f"{name} ({star * difficulty})"


def parse_task_type(text: str) -> typing.Optional[typing.Tuple[str, str]]:
    diffs = len(models.TASK_DIFFICULTY)
    if match := re.match(rf"(?P<name>.+) \((?P<difficulty>.{{1,{diffs}}})\)", text):
        task_type_dict = match.groupdict()
        name = task_type_dict["name"]
        difficulty = models.TASK_DIFFICULTY[len(task_type_dict["difficulty"]) - 1]
        return name, difficulty
    else:
        return None


async def get_task_types_keyboard() -> types.ReplyKeyboardMarkup:
    async with database.sessionmaker() as session:
        async with session.begin():
            task_types_cursor = await session.execute(
                sa.select(models.TaskType).order_by(
                    models.TaskType.difficulty, models.TaskType.name
                )
            )
            task_types = task_types_cursor.all()
    keyboard_markup = types.ReplyKeyboardMarkup(
        row_width=1, one_time_keyboard=True, resize_keyboard=True
    )
    for task_type in task_types:
        keyboard_markup.add(types.KeyboardButton(task_string(task_type[0])))
    return keyboard_markup


async def task_message_lines(
    task: typing.Mapping[str, typing.Any]
) -> typing.Dict[str, str]:
    async with database.sessionmaker() as session:
        async with session.begin():
            task_type_cursor = await session.execute(
                sa.select(models.TaskType).where(models.TaskType.id == task["type_id"])
            )
            task_type_scalar = task_type_cursor.scalar_one()
    payment = _("payment {payment}").format(payment=task["payment"])
    location = _("location {location}").format(location=task["location"])
    time = _("time {time}").format(
        time=datetime.fromisoformat(task["time"]).strftime(DATE_FORMAT)
    )
    contact = _("contact {contact}").format(contact=task["contact"])
    task_type = _("type {type}").format(type=task_string(task_type_scalar))
    return {
        states.TaskCreation.payment._state: payment,
        states.TaskCreation.location._state: location,
        states.TaskCreation.time._state: time,
        states.TaskCreation.contact._state: contact,
        states.TaskCreation.task_type._state: task_type,
    }


async def task_message(task: typing.Mapping[str, typing.Any]) -> str:
    return message_from_lines(await task_message_lines(task))


def skill_levels() -> typing.Tuple[str, ...]:
    levels = (
        _("without_repair"),
        _("with_simple_repair"),
        _("with_electrical_repair"),
    )
    star = emojize(":star:")
    return tuple(f"{star * (i + 1)} {level}" for i, level in enumerate(levels))


async def worker_message_lines(
    worker: typing.Mapping[str, typing.Any]
) -> typing.Dict[str, str]:
    name = _("name {name}").format(name=worker["name"])
    phone = _("phone {phone}").format(
        phone=phonenumbers.format_number(
            phonenumbers.parse(worker["phone"]),
            phonenumbers.PhoneNumberFormat.INTERNATIONAL,
        )
    )
    level = models.WORKER_SKILL.index(worker["skill"])
    skill = _("skill {skill}").format(skill=skill_levels()[level])
    return {
        states.WorkerCreation.name._state: name,
        states.WorkerCreation.phone._state: phone,
        states.WorkerCreation.skill._state: skill,
    }


async def worker_message(worker: typing.Mapping[str, typing.Any]) -> str:
    return message_from_lines(await worker_message_lines(worker))


async def broadcast_task(task: models.Task) -> None:
    async with database.sessionmaker() as session:
        async with session.begin():
            worker_ids_cursor = await session.execute(
                sa.select(models.Worker.id).where(
                    models.Worker.task_id == None  # noqa: E711
                )
            )
            worker_ids = worker_ids_cursor.all()
    message = _("new_task")
    message += "\n" + await task_message(
        {col.name: getattr(task, col.name) for col in task.__table__.columns}
    )
    keyboard_markup = types.InlineKeyboardMarkup()
    keyboard_markup.row(
        types.InlineKeyboardButton(
            _("take_task"), callback_data=take_task_cb.new(task_id=task.id)
        )
    )
    for worker_id in worker_ids:
        for user_id in worker_ids:
            try:
                await bot.send_message(user_id, message, reply_markup=keyboard_markup)
                await asyncio.sleep(0.05)
            except Exception as error:
                logging.getLogger(__name__).error(
                    f"Error sending task {task.id} to worker {user_id}: {error}"
                )
