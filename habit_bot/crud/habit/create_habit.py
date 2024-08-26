
import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from app.db.database import get_async_session
from app.models import User
from habit_bot.bot_init import bot, sent_message_ids
from habit_bot.button_menu import get_user_menu, create_user_menu
from habit_bot.states_group.states import CreateHabit
from services.handlers import create_habit, get_user_by_bot_user_id, record_message_id, \
    clear_message_in_chat, add_job_reminder, validate_time_format, validate_count_day_format

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


async def process_habit_name(message: Message, state: FSMContext):
    """
    Обрабатывает введенное пользователем название привычки.

    Эта функция обновляет состояние пользователя, сохраняет название привычки и
    переходит к следующему шагу - запросу продолжительности выполнения привычки.

    Args:
        message (Message): Сообщение, содержащее название привычки от пользователя.
        state (FSMContext): Контекст состояния для отслеживания состояния пользователя.

    Flow Control:
        - Обновляет данные состояния с введенным названием привычки.
        - Устанавливает новое состояние для ввода продолжительности.
        - Удаляет сообщение пользователя с названием привычки.
        - Отправляет пользователю сообщение с запросом на указание планируемого количества дней.

    Logging:
        - Логирует идентификатор пользователя.
    """
    bot_user_id = message.from_user.id
    await state.update_data(habit_name=message.text)
    await state.set_state(CreateHabit.duration)
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
    sent_message = await message.answer(
        "Укажите планируемое количество дней выполнения заданий _Например 15 или 21_: ",
        parse_mode="Markdown",
    )
    # await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)


async def process_duration(message: Message, state: FSMContext):
    """
    Обрабатывает введенное пользователем количество дней выполнения привычки.

    Эта функция обновляет состояние пользователя, сохраняет количество дней
    и переходит к следующему шагу - запросу описания привычки.

    Args:
        message (Message): Сообщение, содержащее количество дней от пользователя.
        state (FSMContext): Контекст состояния для отслеживания состояния пользователя.

    Flow Control:
        - Обновляет данные состояния с введенным количеством дней.
        - Устанавливает новое состояние для ввода комментариев.
        - Удаляет сообщение пользователя с количеством дней.
        - Отправляет пользователю сообщение с запросом на введение описания привычки.

    Logging:
        - Логирует идентификатор пользователя.
    """
    bot_user_id = message.from_user.id
    duration = message.text
    if validate_count_day_format(duration):
        await state.update_data(duration=duration)
        await state.set_state(CreateHabit.comments)
        try:
            await bot.delete_message(message.chat.id, message.message_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
        # await clear_message_in_chat(message.chat.id, bot_user_id)
        sent_message = await message.answer("Введите описание: ")
#         await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    else:
        try:
            await bot.delete_message(message.chat.id, message.message_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
        sent_message = await message.answer(
            "Неверный формат. Пожалуйста, введите количество дней от 1 до 365.",
            parse_mode="Markdown"
        )
        # await record_message_id(message.chat.id, sent_message.message_id, message.from_user.id)



async def process_comments(message: Message, state: FSMContext):
    """
    Обрабатывает введенное пользователем описание привычки.

    Эта функция обновляет состояние пользователя, сохраняет описание
    и переходит к следующему шагу - запросу времени напоминания.

    Args:
        message (Message): Сообщение, содержащее описание привычки от пользователя.
        state (FSMContext): Контекст состояния для отслеживания состояния пользователя.

    Flow Control:
        - Обновляет данные состояния с введенным описанием.
        - Устанавливает новое состояние для ввода времени напоминания.
        - Удаляет сообщение пользователя с описанием.
        - Отправляет пользователю сообщение с запросом на введение времени напоминания.

    Logging:
        - Логирует идентификатор пользователя.
    """
    bot_user_id = message.from_user.id
    await state.update_data(comments=message.text)
    await state.set_state(CreateHabit.reminder_time)
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
    sent_message = await message.answer(
        "В какое время отправить напоминание?\n _Например 16:00 или 10:30_",
        parse_mode="Markdown"
    )
#     await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)



async def process_reminder_time_and_create_habit(message: Message, state: FSMContext):
    """
    Обрабатывает введенное пользователем время напоминания и создает привычку.

    Эта функция проверяет формат времени, сохраняет введенное время
    и создает новую привычку в базе данных. Если время неправильно,
    отправляет сообщение об ошибке.

    Args:
        message (Message): Сообщение, содержащее время напоминания от пользователя.
        state (FSMContext): Контекст состояния для отслеживания состояния пользователя.

    Flow Control:
        - Удаляет сообщение пользователя с временем напоминания.
        - Проверяет корректность формата времени.
        - Сохраняет время напоминания в состоянии.
        - Если пользователь найден в базе данных, создает привычку и добавляет напоминание.
        - Если время некорректно, отправляет сообщение об ошибке.

    Logging:
        - Логирует идентификатор пользователя и возможные ошибки.
    """
    bot_user_id = message.from_user.id
    logger.info(f"User ID in process_password_and_create_user: {bot_user_id}")
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")

    reminder_time = message.text.strip()
    if validate_time_format(reminder_time):
        await state.update_data(reminder_time=reminder_time)

        user = await get_user_by_bot_user_id(bot_user_id)
        if isinstance(user, User):
            data = await state.get_data()
            data["reminder_time"] = message.text
            data["bot_user_id"] = user.id
            habit_info = data
            await state.clear()
            # await clear_message_in_chat(message.chat.id, bot_user_id)
            # sent_message = await bot.send_message(message.chat.id,
            #                        f"Спасибо! Вот ваши данные:\n"
            #                        f"Название привычки: {habit_info['habit_name']}\n"
            #                        f"Продолжительность: {habit_info['duration']}\n"
            #                        f"Комментарий: {habit_info['comments']}\n"
            #                        f"Отправлять напоминание в - {habit_info['reminder_time']}\n"
            #                        )
#             # await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
            async with get_async_session() as session:
                habit = await create_habit(habit_info, session)
                if habit:
                    sent_message = await bot.send_message(message.chat.id, "Привычка успешно создана", reply_markup=await create_user_menu())
#                     await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
                    logger.info("Отправляем напоминание в работу")
                    job = await add_job_reminder(bot_user_id, habit.reminder_time, habit.habit_name, habit.id)
                    logger.info(f"Результат добавления напоминания - {job}")
                else:
                    sent_message = await bot.send_message(message.chat.id, "При создании привычки произошла ошибка")
#                     await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
        else:
            error_message = "Пользователь не найден в базе данных"
            return error_message

    else:
        sent_message = await message.answer(
            "Неверный формат времени. Пожалуйста, введите время в формате HH:MM.\n _Например 16:00 или 10:30_",
            parse_mode="Markdown"
        )
        # await record_message_id(message.chat.id, sent_message.message_id, message.from_user.id)