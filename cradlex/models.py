import sqlalchemy as sa
import sqlalchemy.ext.asyncio
import sqlalchemy.ext.declarative
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy.types import UserDefinedType


class Point(UserDefinedType):
    def get_col_spec(self):
        return "point"

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        lat, lng = value
        return f"({lng}, {lat})"

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        lng, lat = value
        return float(lat), float(lng)


Base: sa.ext.declarative.DeclarativeMeta = sa.ext.declarative.declarative_base()


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True)
    first_name = sa.Column(sa.Text, nullable=False)
    last_name = sa.Column(sa.Text)
    username = sa.Column(sa.Text)
    state = sa.Column(sa.Text)
    data = sa.Column(JSONB, nullable=False, server_default="{}")


class Worker(Base):
    __tablename__ = "workers"

    id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), primary_key=True)
    name = sa.Column(sa.Text, nullable=False)
    skill = sa.Column(sa.Numeric(1), sa.CheckConstraint("skill BETWEEN 1 AND 3"))
    payment = sa.Column(sa.Integer, sa.CheckConstraint("payment > 0"))

    user = sa.orm.relationship(User)


class TaskType(Base):
    __tablename__ = "task_types"

    id = sa.Column(UUID(), primary_key=True, server_default=sa.func.uuid_generate_v4())
    name = sa.Column(sa.Text, nullable=False)
    difficulty = sa.Column(
        sa.Numeric(1), sa.CheckConstraint("difficulty BETWEEN 1 AND 3")
    )


class Task(Base):
    __tablename__ = "tasks"

    id = sa.Column(UUID(), primary_key=True, server_default=sa.func.uuid_generate_v4())
    location = sa.Column(Point)
    time = sa.Column(sa.TIMESTAMP(timezone=True), default=current_timestamp())
    contact = sa.Column(sa.Text)
    type_id = sa.Column(UUID(), sa.ForeignKey("task_types.id"))
    payment = sa.Column(sa.Integer, sa.CheckConstraint("payment > 0"))
    comments = sa.Column(sa.Text)
    worker_id = sa.Column(sa.Integer, sa.ForeignKey("workers.id"))

    type = sa.orm.relationship(TaskType)
    worker = sa.orm.relationship(Worker)


class TaskMessage(Base):
    __tablename__ = "task_messages"

    id = sa.Column(sa.Integer, primary_key=True)
    task_id = sa.Column(UUID(), sa.ForeignKey("tasks.id"))
    worker_id = sa.Column(sa.Integer, sa.ForeignKey("workers.id"))

    task = sa.orm.relationship(Task)
    worker = sa.orm.relationship(Worker)


class Report(Base):
    __tablename__ = "reports"

    id = sa.Column(UUID(), primary_key=True, server_default=sa.func.uuid_generate_v4())
    task_id = sa.Column(UUID(), sa.ForeignKey("tasks.id"))
    worker_id = sa.Column(UUID(), sa.ForeignKey("workers.id"))
    photo = sa.Column(sa.Text)

    task = sa.orm.relationship(Task)
    worker = sa.orm.relationship(Worker)
