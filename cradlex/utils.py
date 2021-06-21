import asyncio
import logging
import re
import typing
from datetime import datetime

import phonenumbers
import pytz
import sqlalchemy as sa
from aiogram import types
from aiogram.utils.emoji import emojize

from cradlex import callback_data
from cradlex import database
from cradlex import models
from cradlex import states
from cradlex.bot import bot
from cradlex.i18n import _


DATE_FORMAT = "%d.%m %H:%M"


def model_to_dict(
    model: typing.Union[models.Task, models.Worker]
) -> typing.Dict[str, typing.Any]:
    return {col.name: getattr(model, col.name) for col in model.__table__.columns}


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
    if isinstance(task["time"], str):
        task_time = datetime.fromisoformat(task["time"])
    else:
        task_time = task["time"]
    task_time = task_time.astimezone(pytz.timezone("Europe/Moscow"))
    payment = _("payment {payment}").format(payment=task["payment"])
    location = _("location {location}").format(location=task["location"])
    time = _("time {time}").format(time=task_time.strftime(DATE_FORMAT))
    contact = _("contact {contact}").format(contact=task["contact"])
    comment = _("comment {comment}").format(comment=task["comment"])
    task_type = _("type {type}").format(type=task_string(task_type_scalar))
    return {
        states.TaskCreation.payment._state: payment,
        states.TaskCreation.location._state: location,
        states.TaskCreation.time._state: time,
        states.TaskCreation.contact._state: contact,
        states.TaskCreation.comment._state: comment,
        states.TaskCreation.task_type._state: task_type,
    }


async def task_message(
    task: typing.Union[typing.Mapping[str, typing.Any], models.Task]
) -> str:
    if isinstance(task, models.Task):
        task = model_to_dict(task)
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
    if isinstance(worker["phone"], phonenumbers.PhoneNumber):
        worker_phone = worker["phone"]
    else:
        worker_phone = phonenumbers.parse(worker["phone"])
    phone = _("phone {phone}").format(
        phone=phonenumbers.format_number(
            worker_phone,
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


async def worker_message(
    worker: typing.Union[typing.Mapping[str, typing.Any], models.Worker]
) -> str:
    if isinstance(worker, models.Worker):
        worker = model_to_dict(worker)
    return message_from_lines(await worker_message_lines(worker))


async def broadcast_task(task_id: str) -> None:
    async with database.sessionmaker() as session:
        async with session.begin():
            task_cursor = await session.execute(
                sa.select(models.Task, models.TaskType.difficulty)
                .join(models.TaskType)
                .where(models.Task.id == task_id)
            )
            task, task_difficulty = task_cursor.one()
            skill_index = models.TASK_DIFFICULTY.index(task_difficulty)
            worker_ids_cursor = await session.execute(
                sa.select(models.Worker.id).where(
                    models.Worker.task_id == None,  # noqa: E711
                    models.Worker.skill == models.WORKER_SKILL[skill_index],
                )
            )
            worker_ids = worker_ids_cursor.scalars().all()
    text = _("new_task") + "\n" + await task_message(task)
    keyboard_markup = types.InlineKeyboardMarkup()
    keyboard_markup.row(
        types.InlineKeyboardButton(
            _("take_task"),
            callback_data=callback_data.take_task.new(task_id=task.id),
        )
    )
    async with database.sessionmaker() as session:
        async with session.begin():
            for worker_id in worker_ids:
                try:
                    message = await bot.send_message(
                        worker_id, text, reply_markup=keyboard_markup
                    )
                    session.add(
                        models.TaskMessage(
                            id=message.message_id, task_id=task.id, worker_id=worker_id
                        )
                    )
                except Exception as error:
                    logging.getLogger(__name__).error(
                        f"Error sending task {task.id} to worker {worker_id}: {error}"
                    )
                else:
                    await asyncio.sleep(0.05)


async def delete_task_messages(rows: typing.Iterable[sa.engine.Row]) -> None:
    for row in rows:
        await bot.delete_message(chat_id=row.worker_id, message_id=row.id)
        await asyncio.sleep(0.05)
