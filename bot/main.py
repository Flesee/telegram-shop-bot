import asyncio
import sys
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers import main_router
from middlewares import SubscriptionMiddleware
from utils.logger import logger
from database import init_models
from scheduler import setup_scheduler


async def main():
    # Проверка наличия токена
    if not BOT_TOKEN:
        logger.error("Ошибка: BOT_TOKEN не найден в переменных окружения")
        sys.exit(1)
    
    # Инициализация моделей базы данных
    logger.info("Инициализация моделей базы данных...")
    await init_models()
    logger.info("✅ Модели базы данных инициализированы")
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрация middleware
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())
    
    # Регистрация роутеров
    dp.include_router(main_router)
    
    # Запуск бота
    logger.info("✅ Бот запущен")
    
    # Устанавливаем команды бота
    await set_bot_commands(bot)
    
    # Инициализируем и запускаем планировщик
    scheduler = setup_scheduler(bot)
    scheduler.start()
    
    try:
        await dp.start_polling(bot, skip_updates=True, allowed_updates=[
            "message", "callback_query", "inline_query"
        ])
    finally:
        scheduler.shutdown()
        await bot.session.close()


async def set_bot_commands(bot: Bot):
    """Установка команд бота"""
    from aiogram.types import BotCommand
    
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь и FAQ")
    ]
    
    await bot.set_my_commands(commands)
    logger.info("✅ Команды бота установлены")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⛔️ Бот остановлен")
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
