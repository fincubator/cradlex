import sqlalchemy as sa
import sqlalchemy.ext.declarative
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.functions import current_timestamp


TASK_DIFFICULTY = ("easy", "medium", "hard")


Base: sa.ext.declarative.DeclarativeMeta = sa.ext.declarative.declarative_base()


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.BigInteger, primary_key=True)
    first_name = sa.Column(sa.Text, nullable=False)
    last_name = sa.Column(sa.Text)
    username = sa.Column(sa.Text)
    state = sa.Column(sa.Text)
    data = sa.Column(JSONB, nullable=False, server_default="{}")


class Worker(Base):
    __tablename__ = "workers"

    id = sa.Column(sa.BigInteger, sa.ForeignKey("users.id"), primary_key=True)
    name = sa.Column(sa.Text, nullable=False)
    skill = sa.Column(sa.Numeric(1), sa.CheckConstraint("skill BETWEEN 1 AND 3"))
    payment = sa.Column(sa.Integer, sa.CheckConstraint("payment > 0"))


class TaskType(Base):
    __tablename__ = "task_types"

    id = sa.Column(UUID(), primary_key=True, server_default=sa.func.gen_random_uuid())
    name = sa.Column(sa.Text, nullable=False)
    difficulty = sa.Column(sa.Enum(*TASK_DIFFICULTY, name="task_difficulty"))


class Task(Base):
    __tablename__ = "tasks"

    id = sa.Column(UUID(), primary_key=True, server_default=sa.func.gen_random_uuid())
    location = sa.Column(sa.Text)
    time = sa.Column(sa.TIMESTAMP(timezone=True), default=current_timestamp())
    contact = sa.Column(sa.Text)
    type_id = sa.Column(UUID(), sa.ForeignKey("task_types.id"))
    payment = sa.Column(sa.Integer, sa.CheckConstraint("payment > 0"))
    comments = sa.Column(sa.Text)
    worker_id = sa.Column(sa.BigInteger, sa.ForeignKey("workers.id"))


class TaskMessage(Base):
    __tablename__ = "task_messages"

    id = sa.Column(sa.BigInteger, primary_key=True)
    task_id = sa.Column(UUID(), sa.ForeignKey("tasks.id"))
    worker_id = sa.Column(sa.BigInteger, sa.ForeignKey("workers.id"))


class Report(Base):
    __tablename__ = "reports"

    id = sa.Column(UUID(), primary_key=True, server_default=sa.func.gen_random_uuid())
    task_id = sa.Column(UUID(), sa.ForeignKey("tasks.id"))
    worker_id = sa.Column(sa.BigInteger, sa.ForeignKey("workers.id"))
    photo = sa.Column(sa.Text)
