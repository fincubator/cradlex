import sqlalchemy as sa
import sqlalchemy.ext.asyncio

from cradlex import config


with open(config.DATABASE_PASSWORD_FILENAME, "r") as password_file:
    engine = sa.ext.asyncio.create_async_engine(
        "postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}".format(
            host=config.DATABASE_HOST,
            port=config.DATABASE_PORT,
            user=config.DATABASE_USERNAME,
            password=password_file.read().strip(),
            name=config.DATABASE_NAME,
        )
    )


sessionmaker = sa.orm.sessionmaker(engine, class_=sa.ext.asyncio.AsyncSession)
