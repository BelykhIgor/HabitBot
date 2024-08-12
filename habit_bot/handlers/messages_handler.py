import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from habit_bot.crud.habit.create_habit import (
    process_duration,
    process_habit_name,
    process_comments,
    process_reminder_time_and_create_habit
)
from habit_bot.crud.habit.update_habit import (
    update_habit_name,
    update_habit_description,
    update_habit_duration,
    update_habit_reminder,
    save_update_habit
)
from habit_bot.crud.users.auth_user import entering_the_password, sign_in_user
from habit_bot.crud.users.update_user_data import update_username, update_age, update_phone, update_email, update_city, \
    update_user_data
from habit_bot.crud.users.user_registration import (
    process_age,
    process_email,
    process_nickname,
    process_password_and_create_user,
    process_phone
)
from habit_bot.states_group.states import (
    CreateHabit,
    UserEntry,
    UserRegistration,
    UpdateHabit,
    UpdateProfile
    )

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)

router = Router()


@router.message(lambda message: True)
async def handle_message(message: Message, state: FSMContext):
    """
    Обрабатывает входящие сообщения от пользователей в зависимости от их текущего состояния.

    Эта функция асинхронно обрабатывает сообщения от пользователей, определяя
    текущее состояние пользователя в состоянии машины и направляя сообщение в
    соответствующую функцию обработки.

    Args:
        message (Message): Сообщение, отправленное пользователем.
        state (FSMContext): Контекст состояния для отслеживания состояния пользователя.

    Logs:
        - Записывает идентификатор пользователя и текущее состояние в лог.

    Flow Control:
        В зависимости от текущего состояния пользователя (например,
        регистрации, входа, создания привычки, обновления привычки),
        функция вызывает соответствующие обработчики, такие как:
        - `process_nickname`
        - `process_age`
        - `process_phone`
        - `process_email`
        - `process_password_and_create_user`
        - `entering_the_password`
        - `sign_in_user`
        - `process_habit_name`
        - `process_duration`
        - `process_comments`
        - `process_reminder_time_and_create_habit`
        - `update_habit_name`
        - `update_habit_description`
        - `update_habit_duration`
        - `update_habit_reminder`
        - `save_update_habit`

    Эта функция предназначена для обеспечения гибкого и организованного способа управления
    взаимодействиями пользователей с ботом на основе их контекста в рамках
    конечного автомата приложения.
    """
    current_state = await state.get_state()
    bot_user_id = message.from_user.id  # Извлечение идентификатора пользователя
    logger.info(
        f"User ID: {bot_user_id}, Current state: {current_state}")

    if current_state == UserRegistration.nickname:
        await process_nickname(message, state)
    elif current_state == UserRegistration.age:
        await process_age(message, state)
    elif current_state == UserRegistration.phone:
        await process_phone(message, state)
    elif current_state == UserRegistration.email:
        await process_email(message, state)
    elif current_state == UserRegistration.password:
        await process_password_and_create_user(message, state)

    elif current_state == UserEntry.nickname:
        await entering_the_password(message, state)
    elif current_state == UserEntry.password:
        await sign_in_user(message, state)

    elif current_state == CreateHabit.habit_name:
        await process_habit_name(message, state)
    elif current_state == CreateHabit.duration:
        await process_duration(message, state)
    elif current_state == CreateHabit.comments:
        await process_comments(message, state)
    elif current_state == CreateHabit.reminder_time:
        await process_reminder_time_and_create_habit(message, state)

    elif current_state == UpdateHabit.habit_name:
        await update_habit_name(message, state)
    elif current_state == UpdateHabit.habit_description:
        await update_habit_description(message, state)
    elif current_state == UpdateHabit.all_duration:
        await update_habit_duration(message, state)
    elif current_state == UpdateHabit.reminder_time:
        await update_habit_reminder(message, state)
    elif current_state == UpdateHabit.save_update:
        await save_update_habit(state)

    elif current_state == UpdateProfile.fullname:
        await update_username(message, state)
    elif current_state == UpdateProfile.age:
        await update_age(message, state)
    elif current_state == UpdateProfile.phone:
        await update_phone(message, state)
    elif current_state == UpdateProfile.email:
        await update_email(message, state)
    elif current_state == UpdateProfile.city:
        await update_city(message, state)
    elif current_state == UpdateProfile.save_update:
        await update_user_data(state)