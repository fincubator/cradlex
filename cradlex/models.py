import enum
import typing
from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.ext.declarative
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy_utils import PhoneNumberType


TASK_DIFFICULTY = ("easy", "medium", "hard")
WORKER_SKILL = ("no_repair", "simple_repair", "electrical_repair")


class TaskTimeliness(enum.Enum):
    unknown = enum.auto()
    on_time = enum.auto()
    late = enum.auto()
    very_late = enum.auto()


Base = sa.ext.declarative.declarative_base()


class User(Base):
    __tablename__ = "users"

    id: int = sa.Column(sa.BigInteger, primary_key=True)
    first_name: str = sa.Column(sa.Text, nullable=False)
    last_name: str = sa.Column(sa.Text)
    username: str = sa.Column(sa.Text)
    state: str = sa.Column(sa.Text)
    data: typing.Mapping[str, typing.Any] = sa.Column(
        JSONB, nullable=False, server_default="{}"
    )


class Worker(Base):
    __tablename__ = "workers"

    id: int = sa.Column(sa.BigInteger, sa.ForeignKey("users.id"), unique=True)
    phone: str = sa.Column(PhoneNumberType(region="RU"), primary_key=True)
    name: str = sa.Column(sa.Text, nullable=False)
    skill: str = sa.Column(sa.Enum(*WORKER_SKILL, name="worker_skill"), nullable=False)
    payment: int = sa.Column(sa.Integer, sa.CheckConstraint("payment > 0"))
    task_id: str = sa.Column(UUID(), sa.ForeignKey("tasks.id"))


class TaskType(Base):
    __tablename__ = "task_types"

    id: str = sa.Column(
        UUID(), primary_key=True, server_default=sa.func.gen_random_uuid()
    )
    name: str = sa.Column(sa.Text, nullable=False)
    difficulty: str = sa.Column(sa.Enum(*TASK_DIFFICULTY, name="task_difficulty"))


class Task(Base):
    __tablename__ = "tasks"

    id: str = sa.Column(
        UUID(), primary_key=True, server_default=sa.func.gen_random_uuid()
    )
    location: str = sa.Column(sa.Text)
    time: datetime = sa.Column(sa.TIMESTAMP(timezone=True), default=current_timestamp())
    contact: str = sa.Column(sa.Text)
    type_id: str = sa.Column(UUID(), sa.ForeignKey("task_types.id"))
    payment: int = sa.Column(sa.Integer, sa.CheckConstraint("payment > 0"))
    comments: str = sa.Column(sa.Text)
    worker_id: int = sa.Column(sa.BigInteger, sa.ForeignKey("workers.id"))
    timeliness: TaskTimeliness = sa.Column(sa.Enum(TaskTimeliness))
    sent: bool = sa.Column(sa.Boolean)


class TaskMessage(Base):
    __tablename__ = "task_messages"

    id: int = sa.Column(sa.BigInteger, primary_key=True)
    task_id: str = sa.Column(UUID(), sa.ForeignKey("tasks.id"))
    worker_id: int = sa.Column(sa.BigInteger, sa.ForeignKey("workers.id"))


class Report(Base):
    __tablename__ = "reports"

    id: str = sa.Column(
        UUID(), primary_key=True, server_default=sa.func.gen_random_uuid()
    )
    task_id: str = sa.Column(UUID(), sa.ForeignKey("tasks.id"))
    worker_id: int = sa.Column(sa.BigInteger, sa.ForeignKey("workers.id"))
    photo: str = sa.Column(sa.Text)
