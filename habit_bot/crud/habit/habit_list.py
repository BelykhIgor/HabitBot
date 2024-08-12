import logging

from sqlalchemy import and_, desc, select

from app.db.database import get_async_session
from app.models import Habit

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


async def get_habit_list():
    """
    Извлекает список всех привычек из базы данных.

    Эта функция выполняет запрос к базе данных для получения всех записей о привычках
    и возвращает их в виде списка.

    Returns:
        list[Habit]: Список объектов Habit, представляющих все привычки в базе данных.
                      Если привычек нет, возвращает пустой список.

    Flow Control:
        - Логирует начало операции извлечения списка привычек.
        - Выполняет запрос к базе данных для получения всех записей о привычках.
        - Возвращает список привычек.

    Logging:
        - Логирует информацию о начале операции извлечения привычек.
    """
    logger.info(f"Start get_habit_list")
    async with (get_async_session() as session):
        query = select(Habit)
        result = await session.execute(query)
        habit_list = result.scalars().all()
        return habit_list