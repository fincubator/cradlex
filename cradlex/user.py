import sqlalchemy as sa
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware

from cradlex import config
from cradlex import database
from cradlex import models
from cradlex import states


class UserMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update: types.Update, data: dict):
        update_user = None
        if update.message:
            update_user = update.message.from_user
        elif update.callback_query and update.callback_query.message:
            update_user = update.callback_query.from_user
        if update_user:
            database_user = models.User(
                id=update_user.id,
                first_name=update_user.first_name,
                last_name=update_user.last_name,
                username=update_user.username,
            )
            if update_user.id != config.OPERATOR_ID:
                database_user.state = states.Registration.first_message.state
            async with database.sessionmaker() as session:
                async with session.begin():
                    update_result = await session.execute(
                        sa.update(models.User)
                        .where(models.User.id == database_user.id)
                        .values(
                            first_name=database_user.first_name,
                            last_name=database_user.last_name,
                            username=database_user.username,
                        )
                        .returning(sa.text("1"))
                    )
                    if not update_result.one_or_none():
                        session.add(database_user)


user_middleware = UserMiddleware()
