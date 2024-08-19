
import logging
from habit_bot.bot_init import bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from habit_bot.button_menu import update_user_keyboard
from habit_bot.states_group.states import UpdateProfile
from services.handlers import record_message_id, save_update_user_data, validate_age, validate_phone_number, \
    validate_email

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


async def update_username(message: Message, state: FSMContext):
    bot_user_id = message.from_user.id

    await state.update_data(fullname=message.text)
    await state.set_state(UpdateProfile.age)
    sent_message = await message.answer(
        "Хотите еще что то изменить?",
        reply_markup=await update_user_keyboard(bot_user_id),
        parse_mode="Markdown",
    )
    await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)


async def update_age(message: Message, state: FSMContext):
    bot_user_id = message.from_user.id
    age = message.text
    if validate_age(age):
        await state.update_data(age=message.text)
        await state.set_state(UpdateProfile.phone)
        sent_message = await message.answer(
            "Хотите еще что то изменить?",
            reply_markup=await update_user_keyboard(bot_user_id),
            parse_mode="Markdown",
        )
        await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    else:
        await bot.delete_message(message.chat.id, message.message_id)
        sent_message = await message.answer(
            "Неверный формат. Введите ваш возраст цифрами от 1 до 100",
            parse_mode="Markdown"
        )
        await record_message_id(message.chat.id, sent_message.message_id, message.from_user.id)


async def update_phone(message: Message, state: FSMContext):
    bot_user_id = message.from_user.id
    number_phone = message.text
    if validate_phone_number(number_phone):
        await state.update_data(phone=message.text)
        await state.set_state(UpdateProfile.email)
        sent_message = await message.answer(
            "Хотите еще что то изменить?",
            reply_markup=await update_user_keyboard(bot_user_id),
            parse_mode="Markdown",
        )
        await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    else:
        await bot.delete_message(message.chat.id, message.message_id)
        sent_message = await message.answer(
            "Неверный формат. Пожалуйста, введите номер телефона в формате - 89995552211",
            parse_mode="Markdown"
        )
        await record_message_id(message.chat.id, sent_message.message_id, message.from_user.id)


async def update_email(message: Message, state: FSMContext):
    bot_user_id = message.from_user.id
    email = message.text
    if validate_email(email):
        await state.update_data(email=message.text)
        await state.set_state(UpdateProfile.city)
        sent_message = await message.answer(
            "Хотите еще что то изменить?",
            reply_markup=await update_user_keyboard(bot_user_id),
            parse_mode="Markdown",
        )
        await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)
    else:
        await bot.delete_message(message.chat.id, message.message_id)
        sent_message = await message.answer(
            "Неверный формат. Пожалуйста, адрес электронной почты в следующем формате - example@mail.ru",
            parse_mode="Markdown"
        )
        await record_message_id(message.chat.id, sent_message.message_id, message.from_user.id)


async def update_city(message: Message, state: FSMContext):
    bot_user_id = message.from_user.id
    await state.update_data(city=message.text)
    await state.set_state(UpdateProfile.save_update)
    sent_message = await message.answer(
        "Хотите еще что то изменить?",
        reply_markup=await update_user_keyboard(bot_user_id),
        parse_mode="Markdown",
    )
    await record_message_id(message.chat.id, sent_message.message_id, bot_user_id)


async def update_user_data(state: FSMContext):
    data = await state.get_data()
    user_info = {
        "bot_user_id": data.get("bot_user_id"),
        "fullname": data.get("fullname", None),
        "age": data.get("age", None),
        "phone": data.get("phone", None),
        "email": data.get("email", None),
        "city": data.get("city", None),
    }
    logger.info(f"Start save_update_habit - {user_info}")
    await state.clear()
    user = await save_update_user_data(user_info)
    logger.info(f"Save data habit - {user}")
    return user