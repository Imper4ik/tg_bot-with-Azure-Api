import asyncio
import os

import aiogram
import logging
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from app.handlers import router
from dotenv import load_dotenv

# Загрузить переменные окружения из файла .env
load_dotenv()

bot = Bot(token=os.getenv('telegram_bot_token'))

# Инициализация хранилища для FSM (в памяти)
storage = MemoryStorage()

dp = Dispatcher()  # обработка входящих запросов

logging.basicConfig(level=logging.INFO)


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)  # start_polling это функция отправляет запрос в тг бот

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Exit')
