from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from app.handlers import router
from dotenv import load_dotenv

import asyncio
import os
import logging

# Загрузить переменные окружения из файла .env
load_dotenv()

# Проверка наличия токена
telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
if not telegram_token:
    logging.error("Telegram bot token not found in environment variables!")
    exit(1)

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
        logging.error(f"An error occurred: {e}")
        exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Exit')
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        exit(1)
