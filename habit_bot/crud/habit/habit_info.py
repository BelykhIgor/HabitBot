import logging
from services.handlers import get_habit_by_id, get_complected_day

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


async def get_habit_info_by_id(habit_id):
    """
    Получает информацию о привычке по её идентификатору.

    Эта функция извлекает информацию о привычке, включая её название, дату создания,
    описание, общую продолжительность, напоминания, а также количество выполненных и
    невыполненных дней. Если привычка существует, функция возвращает строку с
    детализированной информацией о привычке. Если привычка не найдена, возвращает None.

    Args:
        habit_id (int): Идентификатор привычки, информацию о которой нужно получить.

    Returns:
        str or None: Строка с информацией о привычке, если она найдена; иначе None.
    """
    habit = await get_habit_by_id(habit_id)
    completed_data = await get_complected_day(habit_id)
    if completed_data:
        count_habit_complected = completed_data["completed"]
        count_habit_not_complected = completed_data["not_completed"]
    else:
        count_habit_complected = 0
        count_habit_not_complected = 0

    if habit:
        count_remaining_days = int(habit.duration) - int(habit.count_remained_day)
        habit_info = (f"Формируемая привычка: {habit.habit_name}\n"
                      f"Создана - {habit.created_date}\n"
                      f"Описание - {habit.comments}\n"
                      f"Общая продолжительность дней - {habit.duration}\n"
                      f"Отправлять напоминание в - {habit.reminder_time}\n"
                      f"Выполнено - {count_habit_complected} дней\n"
                      f"Не выполнено - {count_habit_not_complected} дней\n"
                      f"Осталось - {count_remaining_days} дней")
        return habit_info
    return None







