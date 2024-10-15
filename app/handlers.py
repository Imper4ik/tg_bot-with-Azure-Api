from aiogram import F, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from app.conver_voice_in_text import speech_to_text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import app.keyboards as kb
import os

from app.translate_text import translate_text

router = Router()


class TranslateStates(StatesGroup):
    waiting_for_language = State()
    waiting_for_text = State()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer('Hello')
    await message.answer('Список команд: \n '
                         '1 - /start \n'
                         '2 - /show \n'
                         '3 - /url \n'
                         '4 - /help \n'
                         '5 - /Voice_in_text \n'
                         '6 - /Translate', reply_markup=kb.commands_keyboard)


@router.message(F.text)
async def handle_text_commands(message: Message, state: FSMContext):
    print(f"Received command: {message.text}")  # Логируем полученные команды

    # Получаем текущее состояние
    current_state = await state.get_state()

    if current_state == TranslateStates.waiting_for_language.state:
        # Если состояние ожидания языка, обрабатываем ввод как выбор языка
        await choose_language(message, state)
    elif current_state == TranslateStates.waiting_for_text.state:
        # Если состояние ожидания текста, обрабатываем ввод как текст для перевода
        await handle_translate_text(message, state)
    else:
        # Обрабатываем обычные команды
        if message.text == '/start':
            await cmd_start(message)
        elif message.text == '/show':
            await show(message)
        elif message.text == '/url':
            await url(message)
        elif message.text == '/help':
            await get_help(message)
        elif message.text == '/Voice_in_text':
            await request_voice_message(message)
        elif message.text == '/Translate':
            await start_translate(message, state)
        else:
            await message.reply("Неизвестная команда. Пожалуйста, выберите пункт из меню.")


@router.message(Command('show'))
async def show(message: Message):
    await message.reply(f'Привет, твой id: {message.from_user.id}\nИмя: {message.from_user.first_name}')


@router.message(Command('url'))
async def url(message: Message):
    await message.reply('Твои добавленные ссылки:', reply_markup=kb.urls)


@router.message(Command('help'))
async def get_help(message: types.Message):
    await message.answer('Ссылка на телеграмм разработчика: @Mando_Grogu')


@router.message(Command('Voice_in_text'))
async def request_voice_message(message: Message):
    await message.reply('Начните записывать голосовое сообщение (Только на Eng)')


# Обработчик для голосовых сообщений
@router.message(F.voice)
async def handle_voice_message(message: Message):
    voice_file_id = message.voice.file_id
    file_path = await message.bot.get_file(voice_file_id)
    voice_file = f"{voice_file_id}.ogg"
    await message.bot.download_file(file_path.file_path, voice_file)
    text = speech_to_text(voice_file)
    await message.reply(text)

    with open('text', "w+") as voice_file:
        voice_file.write(text)

    os.remove(voice_file)


@router.message(Command('Translate'))
async def start_translate(message: types.Message, state: FSMContext):
    await message.reply("Пожалуйста, выберите язык на который вы хотите перевести (например: 'en', 'pl', 'de').")
    await state.set_state(TranslateStates.waiting_for_language)


# Ожидание ввода языка для перевода
@router.message(TranslateStates.waiting_for_language)
async def choose_language(message: types.Message, state: FSMContext):
    selected_language = message.text.strip().lower()
    # Проверка правильности введенного языка (можете добавить дополнительные проверки)
    if selected_language:
        await state.update_data(selected_language=selected_language)
        await message.reply("Теперь введите текст для перевода.")
        await state.set_state(TranslateStates.waiting_for_text)
    else:
        await message.reply("Некорректный язык. Пожалуйста, введите допустимый код языка (например: 'en', 'pl', 'de').")


# Обработка текста и его перевод
@router.message(TranslateStates.waiting_for_text)
async def handle_translate_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    selected_language = data.get('selected_language')  # Получение выбранного языка
    text_to_translate = message.text
    result = translate_text(text_to_translate, to_langs=[selected_language])

    if result:
        translations = []
        if isinstance(result, list) and len(result) > 0:
            for translation in result[0]['translations']:
                translations.append(f"{translation['to']}: {translation['text']}")

        if not translations:
            await message.reply("Перевод не найден.")
        else:
            await message.reply("\n".join(translations))
    else:
        await message.reply("Ошибка при переводе текста.")

    await state.clear()
