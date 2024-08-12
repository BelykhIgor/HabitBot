
import logging

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.models import User
from services.handlers import get_user_by_bot_user_id

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)

user_state = {}


async def sign_in_menu():
    kb_list = []
    kb_list.append([KeyboardButton(text="📖 Войти")])
    # action = "Войти"
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Воспользуйтесь меню:"
    )
    return keyboard


async def sign_up_menu():
    kb_list = []
    kb_list.append([KeyboardButton(text="👤 Регистрация")])
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Воспользуйтесь меню:"
    )
    return keyboard


async def create_static_main_menu(user):
    logger.info(f"Start create_static_main_menu, user_telegram_id - {user}")
    kb_list = []
    if isinstance(user, User):
       kb_list.append([KeyboardButton(text="📖 Войти")])
       action = "Войти"
    else:
        kb_list.append([KeyboardButton(text="👤 Регистрация")])
        action = "Регистрация"

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Воспользуйтесь меню:"
    )
    return keyboard, action


def get_main_menu():
    markup_main = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вход", callback_data="sign_in"),
         InlineKeyboardButton(text="Регистрация", callback_data="profile")],
    ])
    return markup_main


async def edit_profile_menu(bot_user_id):
    markup_main = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Редактировать", callback_data=f"edit_profile_{bot_user_id}"),
         InlineKeyboardButton(text="Главное меню", callback_data="main_menu")],
    ])
    return markup_main


async def update_user_keyboard(bot_user_id):
    update_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Имя", callback_data=f"user_name_{bot_user_id}")],
        [InlineKeyboardButton(text="Возраст", callback_data=f"user_age_{bot_user_id}")],
        [InlineKeyboardButton(text="Телефон", callback_data=f"user_phone_{bot_user_id}")],
        [InlineKeyboardButton(text="Почта", callback_data=f"user_mail_{bot_user_id}")],
        [InlineKeyboardButton(text="Город", callback_data=f"user_city_{bot_user_id}")],
        [InlineKeyboardButton(text="Сохранить изменения", callback_data=f"save_user_data_{bot_user_id}")],
    ])
    return update_kb


async def create_user_menu():
    kb_list = [
        [KeyboardButton(text="Создать привычку"), KeyboardButton(text="Незавершенные привычки")],
        [KeyboardButton(text="Завершенные привычки"), KeyboardButton(text="Профиль")]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Воспользуйтесь меню:"
    )
    return keyboard



def get_user_menu():
    markup_main = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать привычку", callback_data="add_habit"),
         InlineKeyboardButton(text="Текущие привычки", callback_data="process_habit")],
        [InlineKeyboardButton(text="Сформированные привычки", callback_data="my_habit"),
         InlineKeyboardButton(text="Профиль", callback_data="profile")],

    ])
    return markup_main


async def get_habit_list_menu(habit_list):
    buttons = []
    for habit_item in habit_list:
        button = InlineKeyboardButton(
            text=habit_item.habit_name,
            callback_data=f"habit_item_{habit_item.id}"
        )
        buttons.append([button])  # Оборачиваем кнопку в список для создания строки с одной кнопкой
    button_2 =  [InlineKeyboardButton(text="Создать привычку", callback_data="add_habit"),
     InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
    buttons.append(button_2)
    habit_menu = InlineKeyboardMarkup(inline_keyboard=buttons)
    return habit_menu


async def get_habit_info_menu(habit_id):
    habit_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выполнено", callback_data=f"habit_complected_{habit_id}"),
         InlineKeyboardButton(text="Не выполнено", callback_data=f"habit_not_complected_{habit_id}")],
        [InlineKeyboardButton(text="Редактировать", callback_data=f"update_habit_{habit_id}"),
         InlineKeyboardButton(text="Удалить", callback_data=f"delete_habit_{habit_id}")],
        [InlineKeyboardButton(text="К списку привычек", callback_data="process_habit"),
         InlineKeyboardButton(text="Главное меню", callback_data="main_menu")],
    ])
    return habit_menu


async def get_confirmation_del_habit(habit_id):
    confirmation_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да, удалить", callback_data=f"confirmation_{habit_id}"),
         InlineKeyboardButton(text="Не удалять", callback_data="not_confirmation")]
    ])
    return confirmation_menu



async def create_update_keyboard(habit_id):
    update_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Название формируемой привычки", callback_data=f"habit_name_{habit_id}")],
        [InlineKeyboardButton(text="Описание", callback_data=f"habit_description_{habit_id}")],
        [InlineKeyboardButton(text="Общая продолжительность", callback_data=f"all_duration_{habit_id}")],
        [InlineKeyboardButton(text="Время отправки напоминания", callback_data=f"reminder_time_{habit_id}")],
        [InlineKeyboardButton(text="Сохранить изменения", callback_data=f"update_save_{habit_id}")],
    ])
    return update_kb