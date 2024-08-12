import logging

from app.db.database import get_async_session

from habit_bot.crud.habit.habit_info import get_habit_by_id



logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


async def habit_delete(habit_id):
    """
    Удаляет привычку по заданному идентификатору.

    Эта функция ищет привычку в базе данных по переданному идентификатору и,
    если такая привычка найдена, удаляет её. Если возникает ошибка во время
    удаления, функция возвращает сообщение об ошибке.

    Args:
       habit_id (int): Идентификатор привычки, которую необходимо удалить.

    Returns:
       bool: Возвращает True, если привычка успешно удалена, иначе
             возвращает сообщение об ошибке.

    Flow Control:
       - Логирует начало операции удаления привычки.
       - Пытается получить привычку по идентификатору.
       - Если привычка найдена, удаляет её и коммитит изменения.
       - В случае возникновения ошибки возвращает сообщение об ошибке.

    Logging:
       - Логирует информацию о начале удаления привычки с указанием ее идентификатора.
    """
    logger.info(f"Start delete habit by id- {habit_id}")
    try:
        habit = await get_habit_by_id(habit_id)
        async with get_async_session() as session:
            await session.delete(habit)
            await session.commit()
            return True
    except Exception as e:
        return f"Ошибка удаления привычки из базы данных - {e}"
