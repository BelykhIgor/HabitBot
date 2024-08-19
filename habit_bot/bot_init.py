import logging
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import BotCommand
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import bot_token


logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)

API_TOKEN = bot_token

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler()
# scheduler.start()

sent_message_ids = []


async def set_commands(bot: Bot):
    """
    Устанавливает команды для бота.

    Эта функция определяет список команд, которые будут доступны пользователям
    в интерфейсе бота. Команды помогают пользователям взаимодействовать с ботом
    и находить нужную информацию.

    Параметры:
        bot (Bot): Объект бота, для которого устанавливаются команды.

    Команды:
        - `/start`: Начать взаимодействие с ботом.
        - `/help`: Получить помощь по использованию бота.
        - `/about`: Узнать информацию о боте.
        - `/contact`: Получить контактные данные для связи с разработчиком.

    Примечание:
        Данная функция должна быть вызвана после инициализации бота
        для корректного отображения команд в интерфейсе пользователя.
    """
    commands = [
        BotCommand(command="/start", description="Начать"),
        BotCommand(command="/help", description="Помощь"),
        BotCommand(command="/about", description="О боте"),
        BotCommand(command="/contact", description="Контакты")
    ]
    await bot.set_my_commands(commands)


class CommandCleanupMiddleware(BaseMiddleware):
    """
    Посредник для очистки команд.

    Этот класс реализует посредника, который удаляет командные сообщения
    после их обработки. Это помогает поддерживать чистоту чата,
    избегая накопления команд, которые могут загромождать интерфейс.

    Атрибуты:
       BaseMiddleware (Base): Базовый класс для создания middleware.
    """
    async def __call__(self, handler, event, data):

        """
        Обрабатывает событие и удаляет командное сообщение, если это необходимо.

        Параметры:
            handler: Функция-обработчик, которая будет вызвана для обработки события.
            event: Событие, которое необходимо обработать.
            data: Дополнительные данные, передаваемые в обработчик.

        Возвращает:
            Результат обработки события.
        """
        if isinstance(event, Message) and event.text.startswith('/'):
            response = await handler(event, data)
            await event.delete()
            return response
        else:
            return await handler(event, data)


dp.message.middleware(CommandCleanupMiddleware())