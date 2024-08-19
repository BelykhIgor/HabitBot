
import asyncio
import logging
from aiogram import Dispatcher
from apscheduler.triggers.cron import CronTrigger
from habit_bot.bot_init import bot, dp, set_commands, scheduler
from habit_bot.handlers import commands, callbacks, messages_handler
from habit_bot.run_reminder import check_and_add_jobs
from services.handlers import check_current_day_for_habit



logger: logging.Logger = logging.getLogger(__name__)


def register_routers(dispatcher: Dispatcher):
    dispatcher.include_router(commands.router)
    dispatcher.include_router(callbacks.router)
    dispatcher.include_router(messages_handler.router)


async def start_bot():
    """
    Запускает бота и начинает прослушивание обновлений.

    Функция настраивает уровень логирования, регистрирует маршруты (routers)
    для обработки различных команд и устанавливает команды для бота.
    После этого она начинает опрос обновлений от Telegram с использованием
    метода `start_polling`.

    Returns:
        None
    """
    logging.basicConfig(level=logging.INFO)
    register_routers(dp)
    await set_commands(bot)
    await dp.start_polling(bot)


async def start_scheduler():
    """
    Запускает планировщик для выполнения задач по расписанию.

    Функция настраивает триггер, чтобы задача `check_current_day_for_habit`
    выполнялась каждый день в полночь. После добавления задачи в планировщик
    функция запускает планировщик и регистрирует соответствующее сообщение
    в логах.

    Returns:
       None
    """
    trigger = CronTrigger(hour=0, minute=0)  # Запускать каждый день в полночь
    scheduler.add_job(check_current_day_for_habit, trigger)
    scheduler.start()
    logger.info("Scheduler started every day.")


async def main():
    """
    Основная функция запуска бота и планировщика.

    Эта функция выполняет следующие действия:
    1. Запускает планировщик для периодического выполнения задач.
    2. Проверяет и добавляет незавершенные привычки в планировщик.
    3. Запускает основной цикл обработки сообщений бота.

    В случае возникновения исключений во время выполнения,
    функция регистрирует ошибку в логах и повторно запускает бота.

    Returns:
       None
    """
    try:
        scheduler.start()
        logger.info("Scheduler started successfully.")
        # await start_scheduler()
        await check_and_add_jobs()
        # await scheduler.start()
        await start_bot()
    except Exception as e:
        logger.error(f"Bot polling failed: {e}")
        await start_bot()


# if __name__ == "__main__":
#     asyncio.run(main())

