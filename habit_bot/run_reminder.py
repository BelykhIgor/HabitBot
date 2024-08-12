import logging
import datetime
from sqlalchemy import and_, select
from app.db.database import get_async_session
from app.models import  User, Habit
from services.handlers import add_job_reminder

logger: logging.Logger = logging.getLogger(__name__)


async def check_and_add_jobs():
    """
    Проверяет пользователей на наличие незавершенных привычек и добавляет задачи
    напоминания для них в планировщик.

    Эта функция выполняет автоматическую проверку всех пользователей на наличие
    незавершенных привычек. Если такая привычка найдена, функция добавляет задачу
    на отправку уведомления в планировщик задач.

    Flow Control:
        - Извлекает список всех пользователей из базы данных.
        - Для каждого пользователя:
            - Извлекает незавершенные привычки, у которых осталось время для выполнения.
            - Для каждой незавершенной привычки:
                - Добавляет задачу напоминания в планировщик.
                - Логирует успешное добавление задачи или предупреждение об ошибке.

    Logging:
        - Логирует начало проверки незавершенных задач.
        - Логирует список пользователей.
        - Логирует список незавершенных привычек для каждого пользователя.
        - Логирует успешное добавление задач и любые ошибки, которые могут возникнуть
          при добавлении.

    Exception Handling:
        - Логирует ошибки, возникающие при выполнении запросов к базе данных
          или добавлении задач.
    """
    logger.info("Start автоматической проверки выполненных заданий")
    async with get_async_session() as session:
        try:
            # Получаем список всех пользователей.
            query_user = select(User.id, User.bot_user_id)
            result = await session.execute(query_user)
            user_list = result.fetchall()
            logger.info(f"GET USER list - {user_list}")

            # Проходим циклом по всем пользователям.
            for user in user_list:
                # Собираем список всех незавершенных привычек для данного пользователя.
                query = select(Habit.id, Habit.reminder_time, Habit.habit_name).where(and_(
                    Habit.duration > Habit.count_remained_day,
                    Habit.user_id == user[0]
                ))
                result = await session.execute(query)
                habit_list = result.fetchall()
                logger.info(f"GET Habit ID list - {habit_list}")

                # Добавляем задачу отправки уведомлений в планировщик задач.
                for habit in habit_list:
                    habit_id = habit[0]
                    reminder_time = habit[1]
                    habit_name = habit[2]
                    try:
                        job = await add_job_reminder(bot_user_id=user[1], reminder_time=reminder_time,
                                                     habit_name=habit_name, habit_id=habit_id)
                        if job:
                            logger.info(f"Привычка - {habit_name} добавлена в стек задач ID - {job.id}")
                    except Exception as e:
                        logger.warning(f"Не удалось добавить привычку в стек задач - {habit_name}: {e}")
        except Exception as e:
            logger.error(f"Error during check_and_add_jobs: {e}")


