import sqlalchemy as sa
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware

from cradlex import database
from cradlex import models


class UserMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update: types.Update, data: dict):
        update_user = None
        if update.message:
            update_user = update.message.from_user
        elif update.callback_query and update.callback_query.message:
            update_user = update.callback_query.from_user
        if update_user:
            async with database.sessionmaker() as session:
                async with session.begin():
                    user_cursor = await session.execute(
                        sa.select(models.User).where(models.User.id == update_user.id)
                    )
                    try:
                        database_user = user_cursor.one()[0]
                    except sa.exc.NoResultFound:
                        database_user = models.User(
                            id=update_user.id,
                            first_name=update_user.first_name,
                            last_name=update_user.last_name,
                            username=update_user.username,
                        )
                        session.add(database_user)


user_middleware = UserMiddleware()
