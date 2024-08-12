import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.db.database import get_async_session
from app.models import User
from habit_bot.button_menu import get_user_menu
from habit_bot.run_bot import bot
from habit_bot.states_group.states import UserEntry
from services.handlers import check_username_and_password

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


async def entering_the_password(message: Message, state: FSMContext):
    """
    Запрашивает у пользователя ввод пароля после получения полного имени.

    Эта функция обновляет состояние с полным именем пользователя и
    переходит к следующему состоянию, ожидая ввода пароля.

    Args:
        message (Message): Сообщение от пользователя, содержащее полное имя.
        state (FSMContext): Контекст состояния для сохранения промежуточных данных.

    Flow Control:
        - Обновляет состояние с полным именем пользователя.
        - Устанавливает состояние на ожидание ввода пароля.
        - Отправляет сообщение с запросом на ввод пароля.

    Logging:
        - Не используется.
    """
    await state.update_data(nickname=message.text)
    await state.set_state(UserEntry.password)
    await bot.send_message(message.chat.id, "Введите пароль:", parse_mode='Markdown')


async def sign_in_user(message: Message, state: FSMContext):
    """
    Проверяет введенные учетные данные пользователя и выполняет вход в систему.

    Эта функция обновляет состояние с паролем пользователя,
    проверяет учетные данные, и если они верны, приветствует пользователя.

    Args:
       message (Message): Сообщение от пользователя, содержащее пароль.
       state (FSMContext): Контекст состояния для сохранения промежуточных данных.

    Flow Control:
       - Обновляет состояние с паролем пользователя.
       - Извлекает все данные о пользователе из состояния.
       - Очищает состояние после завершения входа.
       - Проверяет учетные данные пользователя с помощью асинхронной функции.
       - Если вход успешен, отправляет приветственное сообщение пользователю.
       - Если вход неудачен, отправляет сообщение об ошибке.

    Logging:
       - Логирует информацию о пользователе, который пытается войти в систему.
    """
    await state.update_data(password=message.text)
    data = await state.get_data()
    user_info = data
    await state.clear()
    logger.info(f"GET NAME - {user_info}")
    async with get_async_session() as session:
        response = await check_username_and_password(user_info, session)
        if isinstance(response, User):
            # await send_user_welcome(bot, message.chat.id, response)
            await bot.send_message(message.chat.id,
                                   f"Здравствуйте, {response.nickname}! Вы вошли в свой аккаунт.",
                                   reply_markup=get_user_menu()
                                   )
        else:
            await bot.send_message(
                message.chat.id, f"Ошибка:\n{response}", parse_mode="Markdown"
            )
