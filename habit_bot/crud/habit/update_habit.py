
import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from apscheduler.triggers.cron import CronTrigger

from habit_bot.bot_init import scheduler
from habit_bot.button_menu import  create_update_keyboard
from habit_bot.states_group.states import  UpdateHabit
from services.handlers import update_habit_by_id, record_message_id, add_job_reminder, delete_job_reminder, \
    add_sent_message_ids

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


async def update_habit_name(message: Message, state: FSMContext):
    """
    Обновляет название привычки и запрашивает, нужно ли вносить дополнительные изменения.

    Эта функция получает новое название привычки от пользователя,
    обновляет состояние машины состояний и отправляет сообщение с запросом на дальнейшие изменения.

    Args:
       message (Message): Сообщение от пользователя, содержащее новое название привычки.
       state (FSMContext): Контекст состояния для сохранения промежуточных данных.

    Flow Control:
       - Извлекает идентификатор пользователя и текущее состояние.
       - Обновляет название привычки в состоянии.
       - Устанавливает состояние на ожидание дальнейших изменений.
       - Отправляет сообщение с вопросом о дополнительных изменениях.

    Logging:
       - Не используется.
    """
    bot_user_id = message.from_user.id
    data = await state.get_data()
    habit_id = data["habit_id"]
    await state.update_data(habit_name=message.text)
    await state.set_state(UpdateHabit.all_duration)
    sent_message = await message.answer(
        "Хотите еще что то изменить?",
        reply_markup=await create_update_keyboard(habit_id),
        parse_mode="Markdown",
    )
    await add_sent_message_ids(message.chat.id, sent_message.message_id)


async def update_habit_description(message: Message, state: FSMContext):
    """
    Обновляет описание привычки и запрашивает, нужно ли вносить дополнительные изменения.

    Эта функция получает новое описание привычки от пользователя,
    обновляет состояние машины состояний и отправляет сообщение с запросом на дальнейшие изменения.

    Args:
    message (Message): Сообщение от пользователя, содержащее новое описание привычки.
    state (FSMContext): Контекст состояния для сохранения промежуточных данных.

    Flow Control:
    - Извлекает идентификатор пользователя и текущее состояние.
    - Обновляет описание привычки в состоянии.
    - Устанавливает состояние на ожидание дальнейших изменений.
    - Отправляет сообщение с вопросом о дополнительных изменениях.

    Logging:
    - Не используется.
    """
    bot_user_id = message.from_user.id
    await add_sent_message_ids(message.chat.id, message.message_id)
    data = await state.get_data()
    habit_id = data["habit_id"]
    await state.update_data(habit_description=message.text)
    await state.set_state(UpdateHabit.all_duration)
    sent_message = await message.answer(
        "Хотите еще что то изменить?",
        reply_markup=await create_update_keyboard(habit_id),
        parse_mode="Markdown",
    )
    await add_sent_message_ids(message.chat.id, sent_message.message_id)



async def update_habit_duration(message: Message, state: FSMContext):
    """
    Обновляет продолжительность привычки и запрашивает, нужно ли вносить дополнительные изменения.

    Эта функция получает новое значение продолжительности привычки от пользователя,
    обновляет состояние машины состояний и отправляет сообщение с запросом на дальнейшие изменения.

    Args:
        message (Message): Сообщение от пользователя, содержащее новую продолжительность привычки.
        state (FSMContext): Контекст состояния для сохранения промежуточных данных.

    Flow Control:
        - Извлекает идентификатор пользователя и текущее состояние.
        - Обновляет продолжительность привычки в состоянии.
        - Устанавливает состояние на ожидание дальнейших изменений.
        - Отправляет сообщение с вопросом о дополнительных изменениях.

    Logging:
        - Не используется.
    """
    bot_user_id = message.from_user.id
    data = await state.get_data()
    habit_id = data["habit_id"]
    await add_sent_message_ids(message.chat.id, message.message_id)
    await state.update_data(all_duration=message.text)
    await state.set_state(UpdateHabit.reminder_time)
    sent_message = await message.answer(
        "Хотите еще что то изменить?",
        reply_markup=await create_update_keyboard(habit_id),
        parse_mode="Markdown",
    )
    await add_sent_message_ids(message.chat.id, sent_message.message_id)


async def update_habit_reminder(message: Message, state: FSMContext):
    """
    Обновляет время напоминания привычки и запрашивает, нужно ли вносить дополнительные изменения.

    Эта функция получает новое время напоминания от пользователя,
    обновляет состояние машины состояний и отправляет сообщение с запросом на дальнейшие изменения.

    Args:
        message (Message): Сообщение от пользователя, содержащее новое время напоминания.
        state (FSMContext): Контекст состояния для сохранения промежуточных данных.

    Flow Control:
        - Извлекает идентификатор пользователя и текущее состояние.
        - Обновляет время напоминания в состоянии.
        - Устанавливает состояние на ожидание сохранения обновлений.
        - Отправляет сообщение с вопросом о дополнительных изменениях.

    Logging:
        - Не используется.
    """
    bot_user_id = message.from_user.id
    data = await state.get_data()
    habit_id = data["habit_id"]
    await add_sent_message_ids(message.chat.id, message.message_id)
    await state.update_data(reminder_time=message.text)
    await state.update_data(bot_user_id=bot_user_id)
    await state.set_state(UpdateHabit.save_update)
    sent_message = await message.answer(
        "*Хотите еще что то изменить?*",
        reply_markup=await create_update_keyboard(habit_id),
        parse_mode="Markdown",
    )
    await add_sent_message_ids(message.chat.id, sent_message.message_id)


async def save_update_habit(state: FSMContext):
    """
    Сохраняет обновления привычки в базе данных.

    Эта функция извлекает данные об обновлениях привычки из состояния,
    формирует словарь с обновленными данными и сохраняет их в базе данных.

    Args:
        state (FSMContext): Контекст состояния для получения обновленных данных.

    Returns:
        Habit: Объект Habit, представляющий обновленную привычку.

    Flow Control:
        - Извлекает данные о привычке из состояния.
        - Формирует словарь с обновленными данными.
        - Вызывает функцию обновления привычки в базе данных.
        - Очищает состояние.

    Logging:
        - Логирует информацию о начале сохранения обновлений привычки и результат.
    """
    data = await state.get_data()
    habit_info = {
        "habit_id": data.get("habit_id"),
        "bot_user_id": data.get("bot_user_id"),
        "habit_name": data.get("habit_name", None),
        "habit_description": data.get("habit_description", None),
        "all_duration": data.get("all_duration", None),
        "reminder_time": data.get("reminder_time", None),
    }

    logger.info(f"Start save_update_habit - {habit_info}")
    await state.clear()
    bot_user_id = habit_info["bot_user_id"]
    habit = await update_habit_by_id(habit_info)
    logger.info(f"Save data habit - {habit}")
    if habit:
        logger.info("Обновляем напоминание в планировщике.")
        # Ищем задачу в планировщике
        job = scheduler.get_job(habit.id)

        if job:
            # Обновляем существующую задачу
            hour, minute = map(int, habit.reminder_time.split(':'))
            trigger = CronTrigger(hour=hour, minute=minute)
            job.modify(trigger=trigger, args=[bot_user_id, habit.habit_name])
            logger.info(f"Задача {habit.id} успешно обновлена.")
        else:
            # Создаем новую задачу, если она не найдена
            job = await add_job_reminder(bot_user_id, habit.reminder_time, habit.habit_name, habit.id)
            logger.info(f"Создано новое напоминание для задачи - {job}")
    return habit