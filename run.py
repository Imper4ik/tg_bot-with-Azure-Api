from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from app.handlers import router
import os
import logging
import asyncio

# Загрузка переменных окружения
# Для Heroku не используем dotenv, так как Heroku автоматически загружает переменные из Config Vars
# load_dotenv() # Закомментировать или удалить, если не используем .env файл.

# Проверка наличия токена
telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
if not telegram_token:
    logging.error("Telegram bot token not found in environment variables!")
    exit(1)

# Логируем полученный токен (если токен существует, для отладки)
logging.info(f"Telegram bot token loaded: {telegram_token}")

bot = Bot(token=telegram_token)

# Инициализация хранилища для FSM (в памяти)
storage = MemoryStorage()

dp = Dispatcher()  # обработка входящих запросов

logging.basicConfig(level=logging.INFO)


async def main():
    try:
        dp.include_router(router)
        await dp.start_polling(bot)  # start_polling — эта функция отправляет запросы в тг-бот
    except Exception as e:
        logging.error(f"An error occurred during polling: {e}")
        exit(1)

if __name__ == '__main__':
    try:
        logging.info("Starting bot...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Bot stopped by user.')
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        exit(1)
