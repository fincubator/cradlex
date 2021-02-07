from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import DeclarativeMeta

from cradlex import config


Base: DeclarativeMeta = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    state = Column(String)
    data = Column(JSONB, nullable=False, defaut=text("'{}'"))


class Location(Base):
    __tablename__ = "locations"


class Task(Base):
    __tablename__ = "tasks"


class Unit(Base):
    __tablename__ = "units"


class Fund(Base):
    __tablename__ = "funds"


class Report(Base):
    __tablename__ = "reports"


engine = create_async_engine(
    "postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}".format(
        user=config.DATABASE_USER,
        password=config.DATABASE_PASSWORD,
        host=config.DATABASE_HOST,
        port=config.DATABASE_PORT,
        name=config.DATABASE_NAME,
    )
)
