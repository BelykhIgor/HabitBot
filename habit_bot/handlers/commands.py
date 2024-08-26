import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.db.database import get_async_session
from app.models import User
from habit_bot.bot_init import bot
from habit_bot.button_menu import create_user_menu, get_habit_list_menu, sign_in_menu, sign_up_menu, edit_profile_menu
from habit_bot.crud.users.user_info import get_user_info
from habit_bot.states_group.states import UserRegistration, CreateHabit
from services.handlers import  get_completed_habit_list, get_user_by_bot_user_id, get_not_completed_habit_list

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)

router = Router()


@router.message(Command(commands=['start']))
async def start(message: Message):
    """
    Обрабатывает команду '/start' от пользователя.

    Эта функция выполняет следующие действия:
    1. Удаляет командное сообщение пользователя для поддержания чистоты чата.
    2. Проверяет, зарегистрирован ли пользователь в системе.
    3. Если пользователь зарегистрирован, обновляет его chat_id и предлагает войти в систему.
    4. Если пользователь не зарегистрирован, предлагает ему зарегистрироваться.

    Args:
    message (Message): Сообщение от пользователя, содержащие команду '/start'.

    Returns:
    None
    """
    bot_user_id = message.from_user.id
    chat_id = message.chat.id
    logger.warning(f"message.chat.id - {message.chat.id}, message_id - {message.message_id}")
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")

    user = await get_user_by_bot_user_id(bot_user_id)
    # keyboard, action = await create_static_main_menu(user)
    # await clear_message_in_chat(chat_id, bot_user_id)

    if isinstance(user, User):
        logger.warning(f"bot_user_id - {bot_user_id}, chat_id - {message.message_id}")
        async with get_async_session() as session:
            user = await get_user_by_bot_user_id(bot_user_id)
            user.chat_id = chat_id
            session.add(user)
            await session.commit()
        sent_message = await message.answer(
           f"Вы уже зарегистрированы нажмите кнопку 'Войти' ⬇️",
           reply_markup=await sign_in_menu(),
           parse_mode='Markdown',
        )
        # await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    else:
        sent_message = await message.answer(
            "Для работы в системе необходимо зарегистрироваться ⬇️",
            reply_markup=await sign_up_menu(),
            parse_mode='Markdown',
        )
#         await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)


@router.message(Command(commands=['help']))
async def send_help(message: Message):
    """
    Обрабатывает команду '/help' и отправляет пользователю информацию о доступных действиях.

    Эта функция выполняет следующие действия:
    1. Удаляет сообщение с командой '/help' для поддержания чистоты чата.
    2. Очищает чат от предыдущих сообщений пользователя.
    3. Отправляет пользователю сообщение с информацией о функционале бота.

    Args:
       message (Message): Сообщение от пользователя, содержащие команду '/help'.

    Returns:
       None
    """
    bot_user_id = message.from_user.id
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
    try:
        logger.info("Start item Help")
        # await clear_message_in_chat(message.chat.id, bot_user_id)
        sent_message = await message.answer(
            "Я могу отвечать на ваши сообщения. Просто напишите что-нибудь!",
            parse_mode='Markdown'
        )
#         await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    except Exception as e:
        logger.error(f"Error in send_help: {e}")


@router.message(Command(commands=['about']))
async def send_about(message: Message):
    """
    Обрабатывает команду '/about' и отправляет пользователю информацию о сервисе.

    Эта функция выполняет следующие действия:
    1. Удаляет сообщение с командой '/about' для поддержания чистоты чата.
    2. Очищает чат от предыдущих сообщений пользователя.
    3. Отправляет пользователю сообщение с описанием сервиса и его возможностей.

    Args:
        message (Message): Сообщение от пользователя, содержащее команду '/about'.

    Returns:
        None
    """
    bot_user_id = message.from_user.id
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
    try:
        logger.info("Start item About")
#         await clear_message_in_chat(message.chat.id, bot_user_id)
        sent_message = await message.answer(
            "Сервис для эффективного управления и формирования привычек.\n"
            "С помощью данного сервиса можно:\n\n"
            "_-добавлять редактировать или удалять привычки_\n"
            "_-фиксировать выполнение привычек_\n"
            "_-получать оповещения для соблюдения привычек_\n"
            "_-ваши данные под надежной защитой_\n\n"
            "Сервис поможет достичь личные цели на пути самосовершенствования.\n"
            "Телеграм-бот станет удобным инструментом для внедрения полезных привычек в повседневность",
            parse_mode='Markdown'
        )
#         await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    except Exception as e:
        logger.error(f"Error in send_about: {e}")


@router.message(Command(commands=['contact']))
async def send_contact(message: Message):
    """
    Обрабатывает команду '/contact' и отправляет пользователю информацию о сервисе.

    Эта функция выполняет следующие действия:
    1. Удаляет сообщение с командой '/about' для поддержания чистоты чата.
    2. Очищает чат от предыдущих сообщений пользователя.
    3. Отправляет пользователю сообщение с описанием сервиса и его возможностей.

    Args:
        message (Message): Сообщение от пользователя, содержащее команду '/contact'.

    Returns:
        None
    """
    bot_user_id = message.from_user.id
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
#         await clear_message_in_chat(message.chat.id, bot_user_id)
    try:
        logger.info("Start item Contact")
        sent_message = await message.answer(
            "Свяжитесь с нами по адресу: contact@example.com",
            parse_mode='Markdown'
        )
#         await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    except Exception as e:
        logger.error(f"Error in send_contact: {e}")


@router.message(lambda message: message.text == '👤 Регистрация')
async def user_registration(message: Message, state: FSMContext):
    """
    Обрабатывает запрос пользователя на регистрацию.

    Эта функция выполняет следующие действия:
    1. Удаляет сообщение с текстом '👤 Регистрация' для поддержания чистоты чата.
    2. Устанавливает состояние FSM (Finite State Machine) для регистрации пользователя.
    3. Запрашивает у пользователя ввод полного имени и отправляет соответствующее сообщение.

    Args:
       message (Message): Сообщение от пользователя, инициирующее регистрацию.
       state (FSMContext): Контекст состояния для управления состоянием регистрации.

    Returns:
       None
    """
    bot_user_id = message.from_user.id
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
#     await clear_message_in_chat(message.chat.id, bot_user_id)
    await state.set_state(UserRegistration.nickname)
    sent_message = await message.answer("Введите ваш никнейм латинскими буквами:")
#     await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)


@router.message(lambda message: message.text == '📖 Войти')
async def entry_user(message: Message):
    """
    Обрабатывает запрос пользователя на вход в систему.

    Эта функция выполняет следующие действия:
    1. Удаляет сообщение с текстом '📖 Войти' для поддержания чистоты чата.
    2. Отправляет приветственное сообщение пользователю и предоставляет меню с опциями.

    Args:
        message (Message): Сообщение от пользователя, инициирующее вход в систему.

    Returns:
        None
    """
    bot_user_id = message.from_user.id
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
#     await clear_message_in_chat(message.chat.id, bot_user_id)
    sent_message = await message.answer("Добро пожаловать!", reply_markup=await create_user_menu())
#     await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)


@router.message(lambda message: message.text == 'Незавершенные привычки')
async def entry_user(message: Message):
    """
    Обрабатывает запрос пользователя на отображение незавершенных привычек.

    Эта функция выполняет следующие действия:
    1. Удаляет сообщение с текстом 'Незавершенные привычки' для поддержания чистоты чата.
    2. Получает список незавершенных привычек пользователя.
    3. Если у пользователя есть незавершенные привычки, отправляет их список с кнопками для получения подробной информации.
    4. Если незавершенных привычек нет, отправляет сообщение об отсутствии таких привычек.

    Args:
        message (Message): Сообщение от пользователя, инициирующее запрос на отображение незавершенных привычек.

    Returns:
        None
    """
    bot_user_id = message.from_user.id
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")

#     await clear_message_in_chat(message.chat.id, bot_user_id)

    habit_list = await get_not_completed_habit_list(bot_user_id)
    if habit_list != []:
        habit_menu = await get_habit_list_menu(habit_list)
        sent_message = await message.answer(
            "*Ваши текущие привычки:*\n_Для получения подробной информации нажмите на кнопку с названием привычки_",
            reply_markup=habit_menu, parse_mode="Markdown"
        )
#         await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    else:
        sent_message = await message.answer("У вас нет ни одной незавершенной привычки!", reply_markup=await create_user_menu())
#         await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)



@router.message(lambda message: message.text == 'Создать привычку')
async def entry_user(message: Message, state: FSMContext):
    """
    Обрабатывает запрос пользователя на создание новой привычки.

    Эта функция выполняет следующие действия:
    1. Удаляет сообщение с текстом 'Создать привычку' для поддержания чистоты чата.
    2. Устанавливает состояние для ввода названия новой привычки.
    3. Запрашивает у пользователя ввод названия привычки и отправляет соответствующее сообщение.

    Args:
        message (Message): Сообщение от пользователя, инициирующее запрос на создание новой привычки.
        state (FSMContext): Контекст состояния конечного автомата для управления состоянием ввода пользователя.

    Returns:
        None
    """
    bot_user_id = message.from_user.id
    try:
        # Удаление команды от кнопки
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
#     await clear_message_in_chat(message.chat.id, bot_user_id)
    await state.set_state(CreateHabit.habit_name)
    sent_message = await message.answer("Введите название привычки:", parse_mode='Markdown')
#     await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)


@router.message(lambda message: message.text == "Завершенные привычки")
async def completed_habits(message: Message):
    """
    Обрабатывает запрос пользователя на получение списка завершенных привычек.

    Эта функция выполняет следующие действия:
    1. Удаляет сообщение с текстом 'Завершенные привычки' для поддержания чистоты чата.
    2. Получает список завершенных привычек пользователя.
    3. Отправляет пользователю список завершенных привычек или сообщение о том, что таких привычек нет.

    Args:
        message (Message): Сообщение от пользователя, инициирующее запрос на отображение завершенных привычек.

    Returns:
        None
    """
    bot_user_id = message.from_user.id
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
#     await clear_message_in_chat(message.chat.id, bot_user_id)

    completed_list = await get_completed_habit_list(bot_user_id)
    if completed_list is None:
        sent_message = await message.answer(
            "У вас нет еще ни одной завершенной привычки.",
            parse_mode='Markdown',
            reply_markup=await create_user_menu()
        )
#         await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    else:
        completed_habit_menu = await get_habit_list_menu(completed_list)
        sent_message = await message.answer(
            "Список завершенных привычек.",
            parse_mode='Markdown',
            reply_markup=completed_habit_menu
        )
#         await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)



@router.message(lambda message: message.text == 'Профиль')
async def user_info(message: Message):
    logger.info("Start get profile")
    bot_user_id = message.from_user.id
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
#     await clear_message_in_chat(message.chat.id, bot_user_id)
    user_info = await get_user_info(bot_user_id)
    if user_info:
        sent_message = await message.answer(
            f"*Профиль:* \n{user_info}",
            parse_mode='Markdown',
            reply_markup=await edit_profile_menu(bot_user_id),
        )
#         await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
