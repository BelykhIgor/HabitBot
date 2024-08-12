import logging
from services.handlers import get_user_profile

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


async def get_user_info(bot_user_id):
    user = await get_user_profile(bot_user_id)
    if user:
        user_info = (f"*Ник* - `{user.nickname}`\n" if user.nickname else "*Ник*  нет данных\n") + \
                    (f"*Имя* - `{user.fullname}`\n" if user.fullname else "*Имя* - нет данных\n") + \
                    (f"*Возраст* - `{user.age}`\n" if user.age else "*Возраст*- нет данных\n") + \
                    (f"*Телефон* - `{user.phone}`\n" if user.phone else "*Телефон*- нет данных\n") + \
                    (f"*Почта* - `{user.email}`\n" if user.email else "*Почта*- нет данных\n") + \
                    (f"*Город* - `{user.city}`" if user.city else "*Город*- нет данных\n")
        return user_info