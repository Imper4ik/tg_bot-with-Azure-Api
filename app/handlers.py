import time

from aiogram import F, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from dotenv import load_dotenv

from app.conver_voice_in_text import speech_to_text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.text_into_speech import TextToSpeech
from app.translate_text import translate_text, detect_language

import app.keyboards as kb
import os

from app.translated_text_into_speech import process_audio_to_speech

# Загрузить переменные окружения из файла .env
load_dotenv()

router = Router()


# Словарь для хранения времени сообщений пользователей
user_message_times = {}

# Максимальное количество сообщений в минуту
MAX_MESSAGES_PER_MINUTE = 10
TIME_FRAME = 60  # 60 секунд


# Функция для проверки, не превышен ли лимит сообщений
def is_user_spamming(user_id: int) -> bool:
    current_time = time.time()

    if user_id not in user_message_times:
        user_message_times[user_id] = []

    # Очищаем старые записи сообщений (более 1 минуты назад)
    user_message_times[user_id] = [timestamp for timestamp in user_message_times[user_id] if current_time - timestamp < TIME_FRAME]

    # Проверяем, не превышено ли количество сообщений
    if len(user_message_times[user_id]) >= MAX_MESSAGES_PER_MINUTE:
        return True

    # Добавляем временную метку нового сообщения
    user_message_times[user_id].append(current_time)
    return False


class TranslateStates(StatesGroup):
    waiting_for_language = State()
    waiting_for_text = State()


class SpeechStates(StatesGroup):
    waiting_for_language = State()
    waiting_for_gender = State()
    waiting_for_speech_text = State()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer('full commands: \n '
                         '1 - full commands \n'
                         '2 - show your information \n'
                         '3 - links \n'
                         '4 - help \n'
                         '5 - language_interface\n'
                         '6 - Voice_in_text \n'
                         '7 - Translate \n'
                         '8 - Text_to_Speech \n'
                         '9 - handle_audio_to_speech', reply_markup=kb.commands_keyboard)


@router.message(F.text)
async def handle_text_commands(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Проверяем, не превышен ли лимит сообщений
    if is_user_spamming(user_id):
        await message.reply("Вы отправляете слишком много сообщений. Пожалуйста, подождите немного.")
        return

    # Обрабатываем команды или состояния
    current_state = await state.get_state()

    if current_state == TranslateStates.waiting_for_language.state:
        await choose_language(message, state)
    elif current_state == TranslateStates.waiting_for_text.state:
        await handle_translate_text(message, state)
    elif current_state == SpeechStates.waiting_for_language:
        await handle_language_selection(message, state)
    elif current_state == SpeechStates.waiting_for_gender:
        await handle_gender_selection(message, state)
    elif current_state == SpeechStates.waiting_for_speech_text:
        await handle_text_to_speech(message, state)
    else:
        if message.text == 'full commands':
            await cmd_start(message)
        elif message.text == 'show your information':
            await show(message)
        elif message.text == 'links':
            await url(message)
        elif message.text == 'help':
            await get_help(message)
        elif message.text == 'language_interface':
            await language_interface(message)
        elif message.text == 'Voice_in_text':
            await request_voice_message(message)
        elif message.text == 'Translate':
            await start_translate(message, state)
        elif message.text == 'Text_to_Speech':
            await request_language_for_speech(message, state)
        elif message.text == 'handle_audio_to_speech':
            await handle_audio_to_speech(message, state)
        else:
            await message.reply("Неизвестная команда. Пожалуйста, выберите пункт из меню.")


@router.message(Command('show'))
async def show(message: Message):
    await message.reply(f'Привет, твой id: {message.from_user.id}\nИмя: {message.from_user.first_name}')


@router.message(Command('links'))
async def url(message: Message):
    await message.reply('Твои добавленные ссылки:', reply_markup=kb.urls)


@router.message(Command('help'))
async def get_help(message: types.Message):
    await message.answer('Ссылка на телеграмм разработчика: @Mando_Grogu')


@router.message(Command('language_interface'))
async def language_interface(message: types.Message):
    await message.reply("Please choose your language:", reply_markup=kb.language_interface)


@router.callback_query()
async def change_language(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    language_code = call.data.split('_')[1]  # Получаем код языка, например 'en' для английского

    # Сохраняем выбранный язык в FSM
    await state.update_data(language=language_code)

    # Отвечаем пользователю
    if language_code == 'en':
        await call.message.answer("Language set to English. Use /start to see changes.")
    elif language_code == 'ru':
        await call.message.answer("Язык интерфейса изменен на русский. Используйте /start, чтобы увидеть изменения.")
    elif language_code == 'pl':
        await call.message.answer("Język interfejsu zmieniony na polski. Użyj /start, aby zobaczyć zmiany.")

    # Убираем клавиатуру после выбора
    await call.message.edit_reply_markup()


# Обработчик команды /Voice_in_text
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


# Озвучка текста
@router.message(Command('Text_to_Speech'))
async def request_language_for_speech(message: Message, state: FSMContext):
    # Запрашиваем у пользователя язык для озвучивания
    await message.reply("Выберите язык озвучки ('en', 'ru', 'pl', 'de').")
    await state.set_state(SpeechStates.waiting_for_language)


@router.message(SpeechStates.waiting_for_language)
async def handle_language_selection(message: types.Message, state: FSMContext):
    selected_language = message.text.strip().lower()
    if selected_language not in TextToSpeech.VOICE_MAP:
        await message.reply("Неподдерживаемый язык. Пожалуйста, выберите из 'en', 'ru', 'pl', 'de'.")
        return

    await state.update_data(language=selected_language)
    await message.reply("Теперь выберите голос: 'male' или 'female' ('male' недоступен для 'pl').")
    await state.set_state(SpeechStates.waiting_for_gender)


@router.message(SpeechStates.waiting_for_gender)
async def handle_gender_selection(message: types.Message, state: FSMContext):
    selected_gender = message.text.strip().lower()
    data = await state.get_data()
    selected_language = data.get("language")

    # Сохраняем данные языка и пола
    await state.update_data(language=selected_language, gender=selected_gender)
    await message.reply("Введите текст, который вы хотите озвучить.")
    await state.set_state(SpeechStates.waiting_for_speech_text)


@router.message(SpeechStates.waiting_for_speech_text)
async def handle_text_to_speech(message: types.Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language")
    gender = data.get("gender")
    text_to_speech = message.text

    if len(text_to_speech) > 3000:
        await message.reply("Текст слишком длинный. Пожалуйста, введите текст до 3000 символов.")
        return

    tts = TextToSpeech(
        aws_access_key=os.getenv('aws_access_key'),
        aws_secret_key=os.getenv('aws_secret_key'),
        aws_region_name=os.getenv('AWS_DEFAULT_REGION')
    )

    try:
        # Генерация аудиофайла
        output_file = tts.synthesize_speech(text=text_to_speech, language=language, gender=gender)

        # Отправляем аудио в качестве ответа
        await message.reply_audio(FSInputFile(output_file), caption="Вот ваша озвучка текста.")

        # Удаляем временный файл после отправки
        os.remove(output_file)
    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}")

    await state.clear()


@router.message(SpeechStates.waiting_for_speech_text)
async def handle_audio_to_speech(message: types.Message, state: FSMContext):
    # Шаг 1: Распознаем речь из аудиофайла
    if message.audio:
        input_audio_path = f"downloads/{message.audio.file_id}.ogg"
        await message.audio.download(input_audio_path)

        # Вызов функции для конвертации речи в текст
        recognized_text = await speech_to_text(input_audio_path)

        if "Ошибка" in recognized_text:
            await message.answer(f"Произошла ошибка при распознавании речи: {recognized_text}")
            return

        # Шаг 2: Переводим текст
        target_language = await detect_language(recognized_text)
        translated_text = await translate_text(recognized_text, target_language)

        if "Ошибка" in translated_text:
            await message.answer(f"Произошла ошибка при переводе текста: {translated_text}")
            return

        # Отправляем переведенный текст пользователю
        await message.answer(f"Переведенный текст: {translated_text}")
    else:
        await message.answer("Пожалуйста, отправьте аудиофайл для обработки.")


