import re
import typing
from datetime import datetime

import sqlalchemy as sa
from aiogram import types
from aiogram.utils.emoji import emojize

from cradlex import database
from cradlex import models
from cradlex.i18n import _
from cradlex.states import TaskCreation


DATE_FORMAT = "%d.%m.%Y %H:%M"


def task_string(task_type: models.TaskType) -> str:
    name = task_type.name
    difficulty = models.TASK_DIFFICULTY.index(task_type.difficulty) + 1
    star = emojize(":star:")
    return f"{name} ({star * difficulty})"


async def parse_task_type(text: str) -> typing.Optional[typing.Tuple[str, str]]:
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
            task_type_scalar = task_type_cursor.scalar()
    payment = _("payment {payment}").format(payment=task["payment"])
    location = _("location {location}").format(location=task["location"])
    time = _("time {time}").format(
        time=datetime.fromisoformat(task["time"]).strftime(DATE_FORMAT)
    )
    contact = _("contact {contact}").format(contact=task["contact"])
    task_type = _("type {type}").format(type=task_string(task_type_scalar))
    return {
        TaskCreation.payment._state: payment,
        TaskCreation.location._state: location,
        TaskCreation.time._state: time,
        TaskCreation.contact._state: contact,
        TaskCreation.task_type._state: task_type,
    }


def task_message_from_lines(
    lines: typing.Mapping[str, str], numbered: bool = False
) -> str:
    if numbered:
        line_values = [f"{i + 1}. {line}" for i, line in enumerate(lines.values())]
    else:
        line_values = list(lines.values())
    return "\n".join(line_values)


async def task_message(task: typing.Mapping[str, typing.Any]) -> str:
    return task_message_from_lines(await task_message_lines(task))
