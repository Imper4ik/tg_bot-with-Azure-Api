import asyncio
import aiogram
import logging
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from config import telegram_bot_token
from app.handlers import router


bot = Bot(token=telegram_bot_token)

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
