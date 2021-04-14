import json
from string import Template

import sqlalchemy as sa
import sqlalchemy.ext.asyncio
from aiogram.dispatcher.storage import BaseStorage

from cradlex import config
from cradlex import models


URL_TEMPLATE = Template(
    Template("postgresql+asyncpg://$auth@$host:$port/$name").safe_substitute(
        host=config.DATABASE_HOST,
        port=config.DATABASE_PORT,
        name=config.DATABASE_NAME,
    )
)
try:
    with open(config.DATABASE_PASSWORD_FILENAME, "r") as password_file:
        URL = URL_TEMPLATE.substitute(
            auth=f"{config.DATABASE_USERNAME}:{password_file.read().strip()}"
        )
except (AttributeError, FileNotFoundError):
    URL = URL_TEMPLATE.substitute(auth=f"{config.DATABASE_USERNAME}")


engine = sa.ext.asyncio.create_async_engine(URL)
sessionmaker = sa.orm.sessionmaker(
    engine,
    expire_on_commit=False,
    class_=sa.ext.asyncio.AsyncSession,
)


class PostgreStorage(BaseStorage):
    async def close(self):
        pass

    async def wait_closed(self):
        pass

    async def get_state(self, *, chat=None, user, **kwargs):
        async with sessionmaker() as session:
            async with session.begin():
                cursor = await session.execute(
                    sa.select(models.User.state).where(models.User.id == user)
                )
                return cursor.scalar()

    async def get_data(self, *, chat=None, user, **kwargs):
        async with sessionmaker() as session:
            async with session.begin():
                cursor = await session.execute(
                    sa.select(models.User.data).where(models.User.id == user)
                )
                return cursor.scalar()

    async def set_state(self, *, chat=None, user, state=None):
        async with sessionmaker() as session:
            async with session.begin():
                await session.execute(
                    sa.update(models.User)
                    .values(state=state)
                    .where(models.User.id == user)
                )

    async def set_data(self, *, chat=None, user, data):
        async with sessionmaker() as session:
            async with session.begin():
                await session.execute(
                    sa.update(models.User)
                    .values(data=json.dumps(data))
                    .where(models.User.id == user)
                )

    async def update_data(self, *, chat=None, user, data=None, **kwargs):
        if data is None:
            data = {}
        data.update(kwargs)
        async with sessionmaker() as session:
            async with session.begin():
                await session.execute(
                    sa.update(models.User)
                    .values(data=sa.text(f"data || '{json.dumps(data)}'"))
                    .where(models.User.id == user)
                )

    async def reset_state(self, *, chat=None, user, with_data=True):
        values = {"state": None}
        if with_data:
            values["data"] = sa.text("'{}'")
        async with sessionmaker() as session:
            async with session.begin():
                await session.execute(
                    sa.update(models.User)
                    .values(**values)
                    .where(models.User.id == user)
                )
