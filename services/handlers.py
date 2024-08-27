
import logging
import re
from datetime import datetime
import random

import aiogram
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import and_, select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import joinedload
from telebot.formatting import escape_markdown

from app.db.database import get_async_session
from app.models import User, Habit, HabitComplected, MessageControl, SchedulerJobs
from habit_bot.bot_init import bot, sent_message_ids, scheduler

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


async def delete_message_ids(message):
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except aiogram.exceptions.TelegramBadRequest as e:
        if "message to delete not found" in str(e):
            logger.info(f"Message {message.message_id} not found, might have been deleted already.")
        else:
            logger.warning(f"Failed to delete message {message.message_id}: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error when trying to delete message {message.message_id}: {e}")


async def add_sent_message_ids(key, value):
    if key in sent_message_ids:
        sent_message_ids[key].append(value)
    else:
        sent_message_ids[key] = [value]
    return sent_message_ids


async def clear_chat(sent_message_ids, message):
    """
    Функция удаления сообщений из чата.
    Args:
        sent_message_ids: словарь с ID сообщений и чата
    Returns:

    """
    chat_id = message.chat.id
    if chat_id in sent_message_ids:
        for user_id in sent_message_ids[chat_id]:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=user_id)
            except aiogram.exceptions.TelegramBadRequest as e:
                if "message to delete not found" in str(e):
                    logger.info(f"Message {message.message_id} not found, might have been deleted already.")
                else:
                    logger.warning(f"Failed to delete message {chat_id}: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error when trying to delete message {chat_id}: {e}")
        sent_message_ids[chat_id].clear()




async def check_username_and_password(user_data, session: AsyncSession) -> [User, str]:
    """
    Проверяет правильность имени пользователя и пароля.

    Эта функция принимает данные пользователя и проверяет, существует ли пользователь
    с указанным именем (nickname) в базе данных, а также проверяет, соответствует ли
    введённый пароль хранимому паролю. Если пользователь найден и пароль совпадает,
    возвращает объект пользователя. В противном случае возвращает сообщение об ошибке.

    Args:
       user_data (dict): Словарь, содержащий информацию о пользователе с ключами:
                         'nickname' (str) - полное имя пользователя,
                         'password' (str) - пароль пользователя.
       session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Returns:
       User or str: Возвращает объект пользователя, если имя пользователя и пароль верны;
                     иначе возвращает строку с сообщением об ошибке.
    """
    logger.info("Start check user!!!")
    nickname: str = user_data['nickname']
    result = await session.execute(select(User).where(User.nickname == nickname))
    user = result.scalar_one_or_none()
    if user and user.verify_password(user_data['password']):
        logger.info(f"USER - {user}")
        return user
    else:
        error_message = "Неверные имя пользователя или пароль."
        return error_message


async def get_user_profile(bot_user_id: int):
    async with get_async_session() as session:
        query = select(User.nickname, User.fullname, User.phone, User.email, User.age, User.city).where(User.bot_user_id == bot_user_id)
        result = await session.execute(query)
        user = result.fetchone()
        return user



async def create_habit(habit_data, session: AsyncSession) -> [Habit, None]:
    """
    Создает новую привычку в базе данных.

    Эта функция принимает данные о привычке, проверяет, существует ли уже привычка с
    таким же названием, и, если нет, создает новую запись в базе данных. Если привычка
    с таким названием уже существует, возвращает уже существующую привычку.

    Args:
        habit_data (dict): Словарь с данными о привычке, который должен содержать:
                           - 'habit_name' (str): Название привычки.
                           - 'duration' (int): Общая продолжительность привычки в днях.
                           - 'comments' (str): Описание привычки.
                           - 'bot_user_id' (int): Идентификатор пользователя, создавшего привычку.
                           - 'reminder_time' (str): Время, в которое будут отправляться
                             напоминания о привычке.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Returns:
        Habit or None: Возвращает объект Habit, если привычка была успешно создана,
                       или существующий объект Habit, если привычка с таким названием уже существует.
                       Возвращает None в случае ошибки при создании привычки.
    """
    logger.info("Start create_habit!!!")
    habit_name = habit_data["habit_name"]
    try:
        # Проверка на наличие дублирующей записи
        query = select(Habit).filter_by(habit_name=habit_name)
        result = await session.execute(query)
        existing_habit = result.scalars().first()

        if existing_habit:
            logger.warning(f"Привычка  {habit_data['habit_name']} уже существует.")
            return existing_habit
        # Создание новой привычки
        logger.info(f"Время напоминаия - {habit_data["reminder_time"]}")
        new_habit = Habit(
            habit_name=habit_data["habit_name"],
            duration=int(habit_data["duration"]),
            comments=habit_data["comments"],
            user_id=habit_data["bot_user_id"],
            reminder_time=habit_data["reminder_time"],
            created_date=datetime.today().date()
        )
        session.add(new_habit)
        await session.commit()
        await session.refresh(new_habit)

        return new_habit

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Error creating habit: {e}")
        return None

    except Exception as e:
        await session.rollback()
        logger.error(f"An unexpected error occurred: {e}")
        return None


async def create_user(user_data: dict, session: AsyncSession) -> [User, str]:
    """
    Создает нового пользователя в базе данных.

    Эта функция принимает данные о пользователе, проверяет, существует ли уже пользователь
    с таким же идентификатором бота, и, если нет, создает новую запись в базе данных.

    Args:
        user_data (dict): Словарь с данными о пользователе, который должен содержать:
                          - 'nickname' (str): Полное имя пользователя.
                          - 'age' (int): Возраст пользователя.
                          - 'phone' (str): Номер телефона пользователя.
                          - 'email' (str): Электронная почта пользователя.
                          - 'password' (str): Пароль пользователя (предпочтительно хешированный).
                          - 'bot_user_id' (int): Уникальный идентификатор пользователя в системе бота.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Returns:
        User or str: Возвращает объект User, если пользователь был успешно создан,
                      или сообщение об ошибке, если пользователь с таким идентификатором уже существует.
    """
    logger.info("Start create_user!!!")
    try:
        # Проверка на наличие дублирующей записи
        query = select(User).filter_by(bot_user_id=user_data["bot_user_id"])
        result = await session.execute(query)
        existing_user = result.scalars().first()

        if existing_user:
            logger.warning(f"Пользователь уже зарегистрирован, ID: {existing_user.bot_user_id}.")
            error_message = f"Пользователь уже зарегистрирован, ID: {existing_user.bot_user_id}."
            return error_message
        user = User(
            nickname=user_data['nickname'],
            age=user_data['age'],
            phone=user_data['phone'],
            email=user_data['email'],
            password=user_data['password'],
            bot_user_id=user_data['bot_user_id'],
            created_date=datetime.today().date()
        )
        session.add(user)
        await session.commit()
        return user

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Error creating user: {e}")
        return None

    except Exception as e:
        await session.rollback()
        logger.error(f"An unexpected error occurred: {e}")
        return None


async def get_user_id_by_habit_id(habit_id: int) -> [int, None]:
    """
    Получает идентификатор пользователя по идентификатору привычки.

    Эта функция выполняет запрос к базе данных для получения идентификатора пользователя,
    которому принадлежит привычка с указанным идентификатором. Если привычка не найдена,
    возвращает None.

    Args:
        habit_id (int): Уникальный идентификатор привычки.

    Returns:
        int or None: Возвращает идентификатор пользователя, если привычка найдена,
                      иначе возвращает None.
    """
    try:
        async with get_async_session() as session:
            query = select(Habit).where(Habit.id == habit_id)
            result = await session.execute(query)
            habit = result.scalars().one_or_none()
            if habit:
                return habit.user_id
    except Exception as e:
        logger.error(f"Error fetching user by habit_id {habit_id}: {e}")
        return None


async def get_user_by_bot_user_id(bot_user_id: int) -> [int, None]:
    """
    Получает пользователя по его идентификатору бота.

    Эта функция выполняет запрос к базе данных для получения пользователя,
    используя его уникальный идентификатор бота. Если пользователь не найден,
    функция возвращает None.

    Args:
        bot_user_id (int): Уникальный идентификатор пользователя в системе бота.

    Returns:
        User or None: Возвращает объект пользователя, если он найден,
                      иначе возвращает None.

    Raises:
        Exception: Логирует ошибку, если запрос к базе данных не удался.
    """
    try:
        async with get_async_session() as session:
            query = select(User).where(User.bot_user_id == bot_user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            return user
    except Exception as e:
        logger.error(f"Error fetching user by bot_user_id {bot_user_id}: {e}")
        return None


async def create_habit_complected_record(habit_id: int, user_id: int) -> HabitComplected:
    """
    Создает запись о выполнении привычки для указанного пользователя.

    Эта функция добавляет запись о том, что пользователь выполнил
    определенную привычку. Запись включает идентификатор пользователя,
    идентификатор привычки и дату выполнения.

    Args:
        habit_id (int): Уникальный идентификатор привычки, которая была выполнена.
        user_id (int): Уникальный идентификатор пользователя, который выполнил привычку.

    Returns:
        HabitComplected: Возвращает созданную запись о выполненной привычке.

    Raises:
        Exception: Логирует ошибку, если возникает проблема при создании записи в базе данных.
    """
    async with get_async_session() as session:
        async with session.begin():
            complected_record = HabitComplected(
                user_id=user_id,
                habit_id=habit_id,
                created_date=datetime.today().date()
            )
            session.add(complected_record)
            await session.commit()
            return complected_record


async def mark_habit_completed(habit_id: int):
    """
    Отмечает привычку как выполненную для текущего пользователя.

    Эта функция проверяет, была ли привычка уже выполнена пользователем
    в текущий день. Если нет, создается новая запись о выполнении
    привычки, и увеличиваются соответствующие счетчики.

    Args:
        habit_id (int): Уникальный идентификатор привычки, которую нужно отметить как выполненную.

    Returns:
        bool: Возвращает True, если привычка была успешно отмечена как выполненная,
              и False, если привычка уже была выполнена в текущий день.

    Raises:
        ValueError: Если привычка с заданным идентификатором не существует.
    """
    logger.info(f"Start mark_habit_completed, habit_id - {habit_id}")
    current_day = datetime.today().date()
    user_id = await get_user_id_by_habit_id(habit_id)
    if user_id is None:
        # Обработка случая, когда habit_id не существует
        raise ValueError(f"Habit with id {habit_id} does not exist")

    async with get_async_session() as session:
        async with session.begin():
            # Проверка в базе данных уже существующей записи за текущий день
            query = select(HabitComplected).options(joinedload(HabitComplected.habit)).where(and_(
                HabitComplected.habit_id == habit_id,
                HabitComplected.user_id == user_id,
                HabitComplected.created_date == current_day
            ))

            result = await session.execute(query)
            complected = result.scalars().one_or_none()

            # Если записи нет, то создаем новую запись и увеличиваем счетчик
            if complected is None:
                logger.info(f"Записи счетчиков для привычки {habit_id} еще нет. Создаем.")
                habit_complected = await create_habit_complected_record(habit_id, user_id)

                # Увеличиваем счетчик выполненного задания
                habit_complected.increment_count_complected()
                # Получаем запись привычки, увеличиваем кол-во пройденных дней

                habit_query = select(Habit).where(Habit.id == habit_id)
                habit_result = await session.execute(habit_query)
                habit = habit_result.scalars().one_or_none()
                habit.increment_remained_day()

                session.add(habit)
                session.add(habit_complected)
                await session.commit()

                return True
            else:
                return False


async def mark_habit_not_completed(habit_id: int):
    """
    Отмечает привычку как не выполненную для текущего пользователя.

    Эта функция проверяет, была ли привычка уже отмечена как не выполненная
    в текущий день. Если нет, создается новая запись о невыполнении
    привычки, и увеличиваются соответствующие счетчики.

    Args:
        habit_id (int): Уникальный идентификатор привычки, которую нужно отметить как не выполненную.

    Returns:
        bool: Возвращает True, если привычка была успешно отмечена как не выполненная,
              и False, если привычка уже была отмечена как не выполненная в текущий день.

    Raises:
        ValueError: Если привычка с заданным идентификатором не существует.
    """
    logger.info(f"Start mark_habit_not_completed, habit_id - {habit_id}")
    current_day = datetime.today().date()
    user_id = await get_user_id_by_habit_id(habit_id)
    if user_id is None:
        # Обработка случая, когда habit_id не существует.
        raise ValueError(f"Habit with id {habit_id} does not exist")

    async with get_async_session() as session:
        async with session.begin():
            # Проверка в базе данных уже существующей записи за текущий день.
            query = select(HabitComplected).where(and_(
                HabitComplected.habit_id == habit_id,
                HabitComplected.user_id == user_id,
                HabitComplected.created_date == current_day
            ))
            result = await session.execute(query)
            habit_not_complected = result.scalars().one_or_none()

            # Если записи нет, то создаем новую запись и увеличиваем счетчик.
            if habit_not_complected is None:
                logger.info(f"Записи счетчиков для привычки {habit_id} еще нет. Создаем.")
                habit_not_complected = await create_habit_complected_record(habit_id, user_id)
                # Увеличиваем счетчик не выполненного задания.
                habit_not_complected.increment_count_not_complected()

                habit_query = select(Habit).where(Habit.id == habit_id)
                habit_result = await session.execute(habit_query)
                habit = habit_result.scalars().one_or_none()
                habit.increment_remained_day()

                session.add(habit)
                session.add(habit_not_complected)
                await session.commit()
                return True
            else:
                return False


async def get_complected_day(habit_id: int):
    """
    Получает количество выполненных и не выполненных дней для заданной привычки.

    Эта функция извлекает записи о выполнении привычки из базы данных
    по заданному идентификатору привычки и возвращает количество дней,
    когда привычка была выполнена и не выполнена.

    Args:
    habit_id (int): Уникальный идентификатор привычки, для которой необходимо получить
                    количество выполненных и не выполненных дней.

    Returns:
    dict: Словарь с количеством выполненных и не выполненных дней, где:
         - "completed": количество дней, когда привычка была выполнена.
         - "not_completed": количество дней, когда привычка не была выполнена.

         Если записи о привычке не найдены, возвращает None.

    Logs:
    - Записывает информацию о начале выполнения функции, а также
     о получении идентификатора пользователя и записях привычек.

    Raises:
    Exception: Возникает, если происходит ошибка при выполнении запроса к базе данных.
    """
    logger.info("Start rest_of_the_days")
    user_id = await get_user_id_by_habit_id(habit_id)
    logger.info(f"Start rest_of_the_days, get user_id - {user_id}")
    async with get_async_session() as session:
        # Получаем привычку по идентификатору
        query = (
            select(HabitComplected)
            .where(and_(
                HabitComplected.habit_id == habit_id,
                HabitComplected.user_id == user_id,
            ))
        )
        result = await session.execute(query)
        habit_complected = result.scalars().first()
        logger.info(f"Start rest_of_the_days, get habit_complected - {habit_complected}")

        if habit_complected:
            count_complected_day = {
                "completed": habit_complected.count_habit_complected,
                "not_completed": habit_complected.count_habit_not_complected
            }
            return count_complected_day
        else:
            logger.info("habit_complected - НЕ НАЙДЕНО В БАЗЕ")
            return None


async def get_habit_by_id(habit_id: int):
    """
    Получает привычку по её уникальному идентификатору.

    Эта функция выполняет запрос к базе данных для извлечения записи
    привычки на основе заданного идентификатора. Если привычка найдена,
    она возвращается, в противном случае возвращается None.

    Args:
        habit_id (int): Уникальный идентификатор привычки, которую необходимо получить.

    Returns:
        Habit or None: Объект Habit, если привычка найдена, или None, если
                       привычка с указанным идентификатором не найдена.

    Logs:
        - Записывает информацию о начале выполнения функции и результатах запроса.

    Raises:
        Exception: Возникает, если происходит ошибка при выполнении запроса к базе данных.
        """
    async with get_async_session() as session:
        async with session.begin():
            habit_query = select(Habit).where(Habit.id == habit_id)
            habit_result = await session.execute(habit_query)
            habit = habit_result.scalars().one_or_none()
            if habit:
                return habit
            return None


async def record_message_id(chat_id, message_id, user_id):
    """
    Записывает идентификатор сообщения в базу данных.

    Эта функция создает новую запись в таблице управления сообщениями
    для хранения идентификатора сообщения, идентификатора чата и
    идентификатора пользователя. Она может быть использована для отслеживания
    сообщений, отправленных пользователям, и для последующей обработки.

    Args:
       chat_id (int): Идентификатор чата, в котором было отправлено сообщение.
       message_id (int): Идентификатор сообщения, которое нужно записать.
       user_id (int): Идентификатор пользователя, которому принадлежит сообщение.

    Returns:
       None: Функция не возвращает значения, но создает запись в базе данных.

    Logs:
       - Функция может включать логирование для отслеживания успешных
         операций и возможных ошибок (не указано в коде).

    Raises:
       Exception: Может возникнуть ошибка при добавлении записи в базу данных
                  или при выполнении операции commit.
    """
    async with get_async_session() as session:
        message_record = MessageControl(
            chat_id=chat_id,
            message_id=message_id,
            user_id=user_id,
        )
        session.add(message_record)
        await session.commit()


async def clear_message_in_chat(chat_id: int, user_id: int):
    """
    Очищает все сообщения пользователя в указанном чате.

    Эта функция находит и удаляет все сообщения, связанные с данным
    пользователем в указанном чате. После удаления сообщений, соответствующие
    записи удаляются из базы данных.

    Args:
        chat_id (int): Идентификатор чата, из которого необходимо удалить сообщения.
        user_id (int): Идентификатор пользователя, чьи сообщения необходимо удалить.

    Returns:
        None: Функция не возвращает значений, но выполняет операции по удалению
              сообщений и записи их в базу данных.

    Logs:
        - Записывает информацию о найденных сообщениях и о результате попытки
          удаления каждого сообщения.
        - Предупреждает о том, что сообщение уже было удалено, если это
          произошло.
        - Сообщает об ошибках, если удаление сообщения не удалось по причинам,
          отличным от отсутствия сообщения.

    Raises:
        Exception: Может возникнуть ошибка при выполнении операций с базой данных
                   или при попытке удалить сообщение, если возникли проблемы
                   с доступом к Telegram API.
    """
    async with get_async_session() as session:
        query = select(MessageControl).where(
            MessageControl.user_id == user_id,
            MessageControl.user_id == chat_id,
        )
        result = await session.execute(query)
        message_list = result.scalars().all()
        logger.info(f"Message List - {message_list}")
        if message_list:
            for message in message_list:
                try:
                    await bot.delete_message(chat_id, message.message_id)
                    logger.info(f"Сообщение {message.message_id} в чате {chat_id} удалено")
                except Exception as e:
                    if 'message to delete not found' in str(e):
                        logger.warning(f"Сообщение {message.message_id} в чате {chat_id} уже удалено")
                    else:
                        logger.error(f"Не удалось удалить сообщение {message.message_id} из чата {chat_id}: {e}")
        delete_stmt = delete(MessageControl).where(
            MessageControl.user_id == user_id,
            MessageControl.user_id == chat_id,
        )
        await session.execute(delete_stmt)
        await session.commit()


async def update_habit_by_id(habit_info) -> [Habit, None]:
    """
    Обновляет запись привычки по ее идентификатору.

    Эта функция получает данные для обновления привычки и применяет
    изменения в базе данных. Если привычка с указанным идентификатором
    не найдена, функция возвращает None.

    Args:
        habit_info (dict): Словарь, содержащий данные для обновления привычки.
                           Ожидаемые ключи:
                           - "habit_id": Идентификатор привычки (int).
                           - "habit_name": Новое имя привычки (str), если требуется обновление.
                           - "habit_description": Новое описание привычки (str), если требуется обновление.
                           - "all_duration": Новая продолжительность привычки (int), если требуется обновление.
                           - "reminder_time": Новое время напоминания (str), если требуется обновление.

    Returns:
        Habit | None: Возвращает обновленный объект Habit, если обновление прошло успешно.
                      Если привычка с указанным идентификатором не найдена или обновление не удалось,
                      возвращает None.

    Logs:
        - Записывает информацию о привычке перед обновлением.
        - Информирует о неудаче в случае, если запись не найдена или обновление не удалось.

    Raises:
        Exception: Может возникнуть ошибка при выполнении операций с базой данных
                   или при попытке преобразовать идентификатор привычки в int.
    """
    habit_id = habit_info.get("habit_id")
    habit_name = habit_info.get("habit_name")
    habit_description = habit_info.get("habit_description")
    all_duration = habit_info.get("all_duration")
    reminder_time = habit_info.get("reminder_time")
    logger.info(f"HABIT INFO - {habit_name}, {habit_description}, {all_duration}, {reminder_time}")

    async with get_async_session() as session:
        habit = await get_habit_by_id(int(habit_id))
        if habit:
            if habit_name is not None:
                habit.habit_name = habit_name
            if habit_description is not None:
                habit.comments = habit_description
            if all_duration is not None:
                habit.duration = int(all_duration)
            if reminder_time is not None:
                habit.reminder_time = reminder_time

            session.add(habit)
            await session.commit()
            return habit
        else:
            logger.info(f"Что пошло не так при сохранении")
            return None


async def get_completed_habit_list(bot_user_id: int) -> [Habit, None]:
    """
    Получает список завершенных привычек для пользователя по его идентификатору бота.

    Эта функция выполняет запрос к базе данных для получения привычек,
    которые пользователь завершил (т.е. количество оставшихся дней совпадает
    с продолжительностью привычки).

    Args:
        bot_user_id (int): Идентификатор пользователя бота для которого
                            требуется получить список завершенных привычек.

    Returns:
        List[Habit] | None: Возвращает список объектов Habit, представляющих завершенные привычки,
                            если такие есть. Если у пользователя нет завершенных привычек,
                            возвращает None.

    Logs:
        - Записывает информацию о пользователе, чьи завершенные привычки запрашиваются.

    Raises:
        Exception: Может возникнуть ошибка при выполнении операций с базой данных.
    """
    async with get_async_session() as session:
        user = await get_user_by_bot_user_id(bot_user_id)
        logger.info(f"get_completed_habit_list - user_id - {user.id}")
        if user:
            query = select(Habit).where(and_(
                Habit.user_id == user.id,
                Habit.duration == Habit.count_remained_day
            ))
            result = await session.execute(query)
            completed_habit_list = result.scalars().all()
            if completed_habit_list:
                return completed_habit_list
            else:
                return None


async def get_not_completed_habit_list(bot_user_id: int):
    """
    Получает список незавершенных привычек для пользователя по его идентификатору бота.

    Эта функция выполняет запрос к базе данных для получения привычек,
    которые пользователь не завершил (т.е. количество оставшихся дней
    меньше, чем продолжительность привычки).

    Args:
        bot_user_id (int): Идентификатор пользователя бота, для которого
                            требуется получить список незавершенных привычек.

    Returns:
        List[Habit] | None: Возвращает список объектов Habit, представляющих незавершенные привычки,
                            если такие имеются. Если у пользователя нет незавершенных привычек,
                            возвращает None.

    Logs:
        - Записывает информацию о пользователе, чьи незавершенные привычки запрашиваются.

    Raises:
        Exception: Может возникнуть ошибка при выполнении операций с базой данных.
    """
    logger.info(f"Start get_habit_list")
    async with get_async_session() as session:
        user = await get_user_by_bot_user_id(bot_user_id)
        logger.info(f"get_habit_list - bot_user_id - {bot_user_id}")
        logger.info(f"get_habit_list - user_id - {user}")
        if user:
            query = select(Habit).where(and_(
                Habit.user_id == user.id,
                Habit.duration > Habit.count_remained_day
            ))
            result = await session.execute(query)
            completed_habit_list = result.scalars().all()
            return completed_habit_list


async def check_current_day_for_habit():
    """
        Выполняет автоматическую проверку выполненных заданий для всех пользователей.

        Эта функция проверяет все привычки для каждого пользователя и обновляет
        статус их выполнения. Если у пользователя есть незавершенные привычки
        за текущий день, то создается новая запись о невыполненной привычке
        и увеличивается соответствующий счетчик.

        Returns:
            bool: Возвращает True, если запись о невыполненной привычке была создана,
                  иначе возвращает None.

        Logs:
            - Записывает информацию о начале автоматической проверки выполненных заданий.
            - Записывает информацию о создании записи счетчика для привычки, если таковая отсутствует.

        Raises:
            Exception: Может возникнуть ошибка при выполнении операций с базой данных.
        """
    logger.info("Start автоматической проверки выполненных заданий")
    current_day = datetime.today().date()
    async with get_async_session() as session:
        # Получаем список всех пользователей.
        query_user = select(User.id)
        result = await session.execute(query_user)
        user_list = result.scalars().all()
        # Проходим циклом по всем пользователям.
        for user_id in user_list:
        # Собираем список всех незавершенных привычек для данного пользователя
            query = select(Habit.id, Habit.reminder_time, Habit.habit_name).where(and_(
                Habit.duration > Habit.count_remained_day,
                Habit.user_id == user_id
            ))
            result = await session.execute(query)
            habit_list = result.fetchall()

            for habit in habit_list:
                habit_id = habit[0]

                query = select(HabitComplected).where(and_(
                    HabitComplected.habit_id == habit_id,
                    HabitComplected.user_id == user_id,
                    HabitComplected.created_date == current_day
                ))
                result = await session.execute(query)
                habit_complected = result.scalars().one_or_none()
                # Если записи нет, то создаем новую запись и увеличиваем счетчик.
                if habit_complected is None:
                    logger.info(f"Записи счетчиков для привычки {habit} еще нет. Создаем.")
                    habit_not_complected = await create_habit_complected_record(habit_id, user_id)
                    # Увеличиваем счетчик не выполненного задания.
                    habit_not_complected.increment_count_not_complected()

                    habit_query = select(Habit).where(Habit.id == habit_id)
                    habit_result = await session.execute(habit_query)
                    habit = habit_result.scalars().one_or_none()

                    if habit is not None:
                        habit.increment_remained_day()
                        session.add(habit)

                    session.add(habit_not_complected)
                    await session.commit()
                    return True


async def save_update_user_data(user_info):
    logger.info(f"Start UPDATE user data. - {user_info}, {type(user_info)}")
    bot_user_id = user_info.get("bot_user_id")
    fullname = user_info.get("fullname")
    age = user_info.get("age")
    phone = user_info.get("phone")
    email = user_info.get("email")
    city = user_info.get("city")

    logger.info(f"USER INFO - {bot_user_id}, {fullname}, {age}, {phone}, {email}, {city}")

    async with get_async_session() as session:
        user = await get_user_by_bot_user_id(bot_user_id)
        if user:
            if fullname is not None:
                user.fullname = fullname
            if age is not None:
                user.age = age
            if phone is not None:
                user.phone = phone
            if email is not None:
                user.email = email
            if city is not None:
                user.city = city
            session.add(user)
            await session.commit()
            return user
        else:
            logger.info(f"Что пошло не так при сохранении - {user}")
            return None


async def add_job_reminder(bot_user_id, reminder_time, habit_name, habit_id) -> scheduler:
    """
    Добавляет задачу напоминания для заданной привычки.

    Эта функция создает задачу, которая будет отправлять напоминание пользователю
    о привычке в указанное время. Задача добавляется в планировщик с использованием
    формата cron для определения времени.

    Args:
        bot_user_id (int): Идентификатор пользователя бота, которому будет отправлено напоминание.
        reminder_time (str): Время напоминания в формате 'HH:MM'.
        habit_name (str): Название привычки, для которой будет создано напоминание.
        habit_id (int): Идентификатор привычки, связанной с напоминанием.

    Returns:
        Job: Возвращает объект задачи (job) из планировщика, если задача была успешно добавлена,
              иначе возвращает None.

    Logs:
        - Записывает информацию о начале добавления задачи напоминания для заданной привычки.
        - Записывает информацию о найденном пользователе по идентификатору бота.
        - Записывает успешное добавление задачи для привычки.
        - Записывает предупреждение, если пользователь не найден.
        - Записывает информацию об ошибках, возникающих при добавлении задачи.

    Raises:
        Exception: Может возникнуть ошибка при выполнении операций с базой данных или
                    добавлении задачи в планировщик.
    """
    logger.info(f"Start add_job_reminder for habit_id {habit_id}")
    async with get_async_session() as session:
        try:
            hour, minute = map(int, reminder_time.split(':'))
            trigger = CronTrigger(hour=hour, minute=minute)
            job = scheduler.add_job(send_reminder, trigger, args=[bot_user_id, habit_name])

            user = await get_user_by_bot_user_id(bot_user_id)
            if user:
                logger.info(f"Found user {user.id} for bot_user_id {bot_user_id}")
                new_job = SchedulerJobs(job_id=job.id, user_id=user.id, habit_id=habit_id)
                session.add(new_job)
                await session.commit()
                logger.info(f"Job for habit_id {habit_id} added successfully")
                return job
            else:
                logger.warning(f"No user found for bot_user_id {bot_user_id}")
        except Exception as e:
            logger.error(f"Error adding job for habit_id {habit_id}: {e}")
            await session.rollback()


async def delete_job_reminder(habit_id: int):
    """
    Удаляет задачу напоминания для заданной привычки.

    Эта функция ищет задачу напоминания по идентификатору привычки и удаляет
    её из базы данных и планировщика задач. Если задача успешно удалена,
    возвращает True.

    Args:
        habit_id (int): Идентификатор привычки, для которой необходимо удалить задачу напоминания.

    Returns:
        bool: Возвращает True, если задача была успешно удалена, иначе None.

    Logs:
        - Записывает информацию о начале процесса удаления задачи напоминания.
        - Если задача с указанным habit_id не найдена, то не записывает дополнительные логи.

    Raises:
        Exception: Может возникнуть ошибка при выполнении операций с базой данных.
    """
    logger.info(f"Start delete job reminder - habit_id - {habit_id}")
    async with get_async_session() as session:
        query = select(SchedulerJobs).where(SchedulerJobs.habit_id == habit_id)
        result = await session.execute(query)
        job = result.scalars().one_or_none()
        if job:
            await session.delete(job)
            await session.commit()
            return True



async def send_reminder(bot_user_id: int, habit_name):
    """
    Отправляет напоминание пользователю о необходимости выполнения задачи для формирования привычки.

    Эта функция отправляет сообщение пользователю с напоминанием о привычке и
    случайным текстом задания, связанным с этой привычкой. Сообщение отправляется
    в чат пользователя, а идентификатор сообщения записывается в базе данных.

    Args:
        bot_user_id (int): Идентификатор пользователя (бота) в Telegram.
        habit_name (str): Название привычки, для которой отправляется напоминание.

    Returns:
        None: Функция не возвращает значения.

    Logs:
        - Записывает информацию о начале процесса отправки напоминания.
        - Логи не содержат информацию о возможных ошибках отправки сообщений.

    Raises:
        Exception: Может возникнуть ошибка при отправке сообщения или
        при выполнении операций с базой данных.
    """
    async with get_async_session() as session:
        logger.info("Start send_reminder")
        chat_id = bot_user_id
        message = await random_habit()
        sent_message = await bot.send_message(
            chat_id,
            f"`{escape_markdown(message)}`\n\nДля формирования привычки - *{habit_name}* необходимо выполнить задание!",
            parse_mode='Markdown',
        )
        await record_message_id(chat_id, sent_message.message_id, bot_user_id)


async def random_habit():
    """
    Извлекает случайную мудрость о привычках из файла и логирует ее.

    Эта асинхронная функция открывает файл, содержащий советы или мудрости о
    привычках, выбирает случайную строку и возвращает ее. Если файл не удается
    открыть или возникает ошибка, функция логирует сообщение об ошибке.

    Returns:
       str: Случайная мудрость о привычках, если операция успешна.
       None: Если возникает ошибка при загрузке файла.

    Logs:
       - Записывает информацию о начале процесса извлечения мудрости.
       - Записывает извлеченную мудрость с экранированием Markdown.
       - Логирует ошибку, если файл не может быть загружен.
    """
    logger.info("Start random_habit")
    file_path = "./habit_bot/wisdom_about_habits.txt"
    try:
        with open(file_path, "r", encoding="UTF-8") as file:
            habit =file.read().split("\n")
            answer = random.choice(habit)
            logger.info(f"GET Wisdom - {escape_markdown(answer)}")
            return answer
    except Exception as e:
        logger.error(f"Error loading wisdom_about_habits: {e}")


# Валидация входящих данных.
def validate_time_format(time_str):
    """
    Проверяет, соответствует ли строка формату времени 'HH:MM'.

    Эта функция принимает строку и проверяет, соответствует ли она формату
    времени 'HH:MM', где 'HH' - часы (00-23), а 'MM' - минуты (00-59).
    Если строка соответствует формату, функция возвращает True, в противном
    случае - False.

    Args:
        time_str (str): Строка времени для проверки.

    Returns:
        bool: True, если строка соответствует формату времени 'HH:MM',
              иначе False.
    """
    pattern = re.compile(r'^\d{2}:\d{2}$')
    if not pattern.match(time_str):
        return False
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def validate_count_day_format(count_day):
    pattern = re.compile(r'^(?:[1-9]|[1-9][0-9]|[12][0-9]{2}|3[0-5][0-9]|36[0-5])$')
    if not pattern.match(count_day):
        return False
    return True


def validate_username(user_name):
    pattern = re.compile(r'^[a-zA-Z]+$')
    if not pattern.match(user_name):
        return False
    return True


def validate_phone_number(phone_number):
    pattern = re.compile(r'^8\d{10}$')
    if not pattern.match(phone_number):
        return False
    return True

def validate_email(email):
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not pattern.match(email):
        return False
    return True


def validate_age(age):
    pattern = re.compile(r'^(?:[1-9]|[1-9][0-9])$')
    if not pattern.match(age):
        return False
    return True


def validate_password(password):
    pattern = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    if not pattern.match(password):
        return False
    return True