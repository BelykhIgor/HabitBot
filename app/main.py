import asyncio
import datetime
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
import sentry_sdk
import logging

from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app.db.database import get_async_session, engine, Base
from config import APP_PORT
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from habit_bot.run_bot import start_bot

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)

sentry_sdk.init(
    dsn="https://a2cda3c5e65fa2d04110efc79ccd050d@o4507460360667136.ingest.us.sentry.io/4507757806223360",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Запускает процесс создания тестовых данных.

    Эта функция асинхронного контекстного менеджера
    управляет настройкой тестовых данных,
    включая:
    - Создание необходимых таблиц базы данных.

    Parameters:
        app (FastAPI): Экземпляр приложения Fast API.

    Yields:
        None: Эта функция не выдает никакого значения.
    """
    async with get_async_session() as session:
        # await create_table()
        bot_task = asyncio.create_task(start_bot())
    yield
    bot_task.cancel()
    await engine.dispose()


def create_app() -> FastAPI:
    """
    Создает и настраивает приложение Fast API.

    Returns:
        FastAPI: Сконфигурированный экземпляр приложения Fast API.
    """
    app = FastAPI(lifespan=lifespan)
    return app


async def create_table():
    """
    Создает таблицы базы данных для тестовых данных.

    Эта функция удаляет таблицу с идентификаторами напоминаний, и создает новую.
    """
    async with engine.begin() as conn:
        logger.info("Dropping scheduler_jobs table")
        logger.info("Drop all tables")
        await conn.run_sync(Base.metadata.drop_all)
        # await conn.run_sync(SchedulerJobs.__table__.drop, checkfirst=True)
        await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created successfully")
        logger.info("Creating scheduler_jobs table")
        # await conn.run_sync(SchedulerJobs.__table__.create)



async def create_test_user(session: AsyncSession):
    """
    Создает тестовых пользователей.

    Эта функция создает двух тестовых пользователей со следующими данными:
    - Пользователь 1: Ник "admin", пароль "admin".

    Parameters:
        session (AsyncSession):
        Асинхронный сеанс для взаимодействия с базой данных.

    Returns:
        Tuple[User, User]:
        Возвращает экземпляр пользователя User.
    """
    logger.info("Start create test user")
    first_user = User(
        nickname="admin",
        age="35",
        phone="+79264445533",
        email="example@mail.ru",
        password="admin",
        bot_user_id=1143588687,
        created_date = datetime.date.today()
    )
    session.add(first_user)
    await session.commit()
    return first_user

app = create_app()
app.add_middleware(SentryAsgiMiddleware)


def start_app():
    uvicorn.run("main:app", host="127.0.0.1", port=int(APP_PORT), reload=True)


if __name__ == "__main__":
    start_app()
