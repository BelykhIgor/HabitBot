
import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from app.db.database import get_async_session
from app.models import User
from habit_bot.bot_init import bot, sent_message_ids
from habit_bot.button_menu import get_user_menu, get_main_menu
from habit_bot.states_group.states import UserRegistration
from services.handlers import create_user, record_message_id, clear_message_in_chat, validate_username, \
    validate_phone_number, validate_email, validate_password, validate_age

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


# Сбор данных для регистрации нового пользователя
async def process_nickname(message: Message, state: FSMContext):
    """
    Обрабатывает ввод полного имени пользователя и переходит к следующему шагу.

    Эта функция обновляет состояние с полным именем пользователя и
    запрашивает ввод возраста.

    Args:
        message (Message): Сообщение от пользователя, содержащее полное имя.
        state (FSMContext): Контекст состояния для сохранения промежуточных данных.

    Flow Control:
        - Обновляет состояние с полным именем пользователя.
        - Устанавливает состояние на ожидание ввода возраста.
        - Удаляет сообщение пользователя.
        - Отправляет сообщение с запросом на ввод возраста.

    Logging:
        - Не используется.
    """
    bot_user_id = message.from_user.id
    user_name = message.text
    if validate_username(user_name):
        await state.update_data(nickname=message.text)
        await state.set_state(UserRegistration.age)
        await bot.delete_message(message.chat.id, message.message_id)
        sent_message = await message.answer("Введите ваш возраст: ")
        await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    else:
        await bot.delete_message(message.chat.id, message.message_id)
        sent_message = await message.answer(
            "Неверный формат. Пожалуйста, введите имя без цифр и спецсимволов.",
            parse_mode="Markdown"
        )
        await record_message_id(message.chat.id, sent_message.message_id, message.from_user.id)


async def process_age(message: Message, state: FSMContext):
    """
    Обрабатывает ввод возраста пользователя и переходит к следующему шагу.

    Эта функция обновляет состояние с возрастом пользователя и
    запрашивает ввод номера телефона.

    Args:
        message (Message): Сообщение от пользователя, содержащее возраст.
        state (FSMContext): Контекст состояния для сохранения промежуточных данных.

    Flow Control:
        - Обновляет состояние с возрастом пользователя.
        - Устанавливает состояние на ожидание ввода номера телефона.
        - Удаляет сообщение пользователя.
        - Отправляет сообщение с запросом на ввод номера телефона.

    Logging:
        - Не используется.
    """
    bot_user_id = message.from_user.id
    age = message.text
    if validate_age(age):
        await state.update_data(age=message.text)
        await state.set_state(UserRegistration.phone)
        await bot.delete_message(message.chat.id, message.message_id)
        sent_message = await message.answer("Введите номер вашего телефона: ")
        await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    else:
        await bot.delete_message(message.chat.id, message.message_id)
        sent_message = await message.answer(
            "Неверный формат. Введите ваш возраст цифрами от 1 до 100",
            parse_mode="Markdown"
        )
        await record_message_id(message.chat.id, sent_message.message_id, message.from_user.id)



async def process_phone(message: Message, state: FSMContext):
    """
    Обрабатывает ввод номера телефона пользователя и переходит к следующему шагу.

    Эта функция обновляет состояние с номером телефона пользователя и
    запрашивает ввод адреса электронной почты.

    Args:
        message (Message): Сообщение от пользователя, содержащее номер телефона.
        state (FSMContext): Контекст состояния для сохранения промежуточных данных.

    Flow Control:
        - Обновляет состояние с номером телефона пользователя.
        - Устанавливает состояние на ожидание ввода адреса электронной почты.
        - Удаляет сообщение пользователя.
        - Отправляет сообщение с запросом на ввод адреса электронной почты.

    Logging:
        - Не используется.
    """
    bot_user_id = message.from_user.id
    number_phone = message.text
    if validate_phone_number(number_phone):
        await state.update_data(phone=message.text)
        await state.set_state(UserRegistration.email)
        await bot.delete_message(message.chat.id, message.message_id)
        sent_message = await message.answer("Введите адрес электронной почты: ")
        await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    else:
        await bot.delete_message(message.chat.id, message.message_id)
        sent_message = await message.answer(
            "Неверный формат. Пожалуйста, введите номер телефона в формате - 89995552211",
            parse_mode="Markdown"
        )
        await record_message_id(message.chat.id, sent_message.message_id, message.from_user.id)

async def process_email(message: Message, state: FSMContext):
    """
    Обрабатывает ввод адреса электронной почты пользователя и переходит к следующему шагу.

    Эта функция обновляет состояние с адресом электронной почты пользователя и
    запрашивает ввод пароля.

    Args:
        message (Message): Сообщение от пользователя, содержащее адрес электронной почты.
        state (FSMContext): Контекст состояния для сохранения промежуточных данных.

    Flow Control:
        - Обновляет состояние с адресом электронной почты пользователя.
        - Устанавливает состояние на ожидание ввода пароля.
        - Удаляет сообщение пользователя.
        - Отправляет сообщение с запросом на ввод пароля.

    Logging:
        - Не используется.
    """
    bot_user_id = message.from_user.id
    email = message.text
    if validate_email(email):
        await state.update_data(email=message.text)
        await state.set_state(UserRegistration.password)
        await bot.delete_message(message.chat.id, message.message_id)
        sent_message = await message.answer("Придумайте пароль\n"
                             "_пароль должен содержать не менее 8 символов, одну заглавную букву, один спецсимвол:_ ",
                             parse_mode='Markdown',
                             )
        await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    else:
        await bot.delete_message(message.chat.id, message.message_id)
        sent_message = await message.answer(
            "Неверный формат. Пожалуйста, адрес электронной почты в следующем формате - example@mail.ru",
            parse_mode="Markdown"
        )
        await record_message_id(message.chat.id, sent_message.message_id, message.from_user.id)


async def process_password_and_create_user(message: Message, state: FSMContext):
    """
    Обрабатывает ввод пароля пользователя и создает нового пользователя в системе.

    Эта функция обновляет состояние с паролем пользователя, собирает все
    данные для создания нового пользователя и отправляет сообщение с
    подтверждением.

    Args:
       message (Message): Сообщение от пользователя, содержащее пароль.
       state (FSMContext): Контекст состояния для сохранения промежуточных данных.

    Flow Control:
       - Обновляет состояние с паролем пользователя.
       - Извлекает все данные о пользователе из состояния.
       - Очищает состояние после завершения регистрации.
       - Удаляет сообщение пользователя.
       - Отправляет сообщение с данными пользователя.
       - Создает нового пользователя в базе данных.
       - Если создание пользователя успешно, отправляет приветственное сообщение.
       - Если создание пользователя не удалось, отправляет сообщение об ошибке и
         предлагает повторить попытку.

    Logging:
       - Логирует идентификатор пользователя при создании.
    """
    bot_user_id = message.from_user.id
    password = message.text
    if validate_password(password):
        logger.info(f"User ID in process_password_and_create_user: {bot_user_id}")
        data = await state.get_data()
        data["password"] = message.text
        data["bot_user_id"] = bot_user_id
        user_info = data
        await state.clear()
        await bot.delete_message(message.chat.id, message.message_id)
        await clear_message_in_chat(message.chat.id, bot_user_id)
        sent_message = await bot.send_message(message.chat.id,
                               f"Спасибо! Вот ваши данные:\n"
                               f"Имя: {user_info['nickname']}\n"
                               f"Возраст: {user_info['age']}\n"
                               f"Номер телефона: {user_info['phone']}\n"
                               f"Адрес электронной почты: {user_info['email']}\n"
                               f"User_ID: {user_info['bot_user_id']}"
                               )
        await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)

        async with get_async_session() as session:
            response = await create_user(user_info, session=session)
            if isinstance(response, User):
                sent_message = await bot.send_message(
                    message.chat.id, f"Добро пожаловать в нашу команду {response.nickname}!",
                    reply_markup=get_user_menu()
                )
                await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
            else:
                sent_message = await bot.send_message(message.chat.id, f"Ошибка:\n{response}")
                sent_message_ids.append(sent_message.message_id)
                sent_message = await bot.send_message(message.chat.id,
                                       "Давайте попробуем еще раз! Нажмите 'Вход' или 'Регистрация'.",
                                       reply_markup=get_main_menu(),
                                       parse_mode='Markdown',
                                       )
                await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    else:
        await bot.delete_message(message.chat.id, message.message_id)
        sent_message = await message.answer(
            "Неверный формат. _пароль должен содержать не менее 8 символов, одну заглавную букву, один спецсимвол:_ ",
            parse_mode="Markdown"
        )
        await record_message_id(message.chat.id, sent_message.message_id, message.from_user.id)