import time

from aiogram import F, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from dotenv import load_dotenv

from app.conver_voice_in_text import speech_to_text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter


from app.text_into_speech import TextToSpeech
from app.translate_text import translate_text, detect_language

import app.keyboards as kb
import os
import logging


logging.basicConfig(
    level=logging.INFO,  # Установите DEBUG для детального логирования
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="bot_debug.log",  # Логи будут сохраняться в файл
    filemode="w"  # Перезапись файла при каждом запуске
)


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
    waiting_for_language_to_speech = State()
    waiting_for_text = State()


class SpeechStates(StatesGroup):
    waiting_for_language = State()
    waiting_for_gender = State()
    waiting_for_speech_text = State()
    waiting_for_audio = State()
    waiting_for_gender_to_speech = State()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer('full commands: \n '
                         '1 - full commands \n'
                         '2 - show your information \n'
                         '3 - links \n'
                         '4 - help \n'
                         '5 - Voice_in_text \n'
                         '6 - Translate \n'
                         '7 - Text_to_Speech \n'
                         '8 - handle_audio_to_speech', reply_markup=kb.commands_keyboard)


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
    elif current_state == SpeechStates.waiting_for_audio:
        await process_audio(message, state)
    elif current_state == TranslateStates.waiting_for_language_to_speech:
        await choose_language_for_audio(message, state)
    elif current_state == SpeechStates.waiting_for_gender_to_speech:
        await choose_voice_and_speak(message, state)
    else:
        if message.text == 'full commands':
            await cmd_start(message)
        elif message.text == 'show your information':
            await show(message)
        elif message.text == 'links':
            await url(message)
        elif message.text == 'help':
            await get_help(message)
        elif message.text == 'Voice_in_text':
            await request_and_handle_voice_message(message)
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


# Обработчик команды /Voice_in_text
@router.message(Command('Voice_in_text'))
async def request_and_handle_voice_message(message: Message):
    await message.reply('Начните записывать голосовое сообщение (Только на Eng)')

    # Ожидание голосового сообщения
    @router.message(lambda m: m.voice)
    async def handle_voice_message(message: Message):
        voice_file_id = message.voice.file_id
        file_path = await message.bot.get_file(voice_file_id)
        voice_file = f"{voice_file_id}.ogg"

        await message.bot.download_file(file_path.file_path, voice_file)

        # Функция преобразования речи в текст
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

    # Проверка на допустимость выбранного пола для языка
    if selected_language == 'pl' and selected_gender == 'male':
        await message.reply("Для польского языка доступен только женский голос. Пожалуйста, выберите 'female'.")
        return
    elif selected_gender not in ['male', 'female']:
        await message.reply("Ошибка: Пожалуйста, выберите 'male' или 'female'. Попробуйте снова.")
        return  # Ожидаем новый ввод от пользователя

    # Сохраняем данные языка и пола
    await state.update_data(language=selected_language, gender=selected_gender)

    # Переходим к следующему шагу
    await message.reply("Теперь введите текст, который вы хотите озвучить.")
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


@router.message(Command('handle_audio_to_speech'))
async def handle_audio_to_speech(message: Message, state: FSMContext):
    logging.info(f"Получена команда /handle_audio_to_speech от пользователя {message.from_user.id}")
    await message.reply("Пожалуйста, запишите голосовое сообщение (Eng).")
    await state.set_state(SpeechStates.waiting_for_audio)
    logging.info("Установлено состояние: waiting_for_audio")


@router.message(SpeechStates.waiting_for_audio)
async def process_audio(message: Message, state: FSMContext):
    try:
        logging.info(f"Получено голосовое сообщение от пользователя {message.from_user.id}")
        voice_file_id = message.voice.file_id
        logging.debug(f"Voice file ID: {voice_file_id}")

        file_path = await message.bot.get_file(voice_file_id)
        logging.info(f"Получен путь к файлу: {file_path.file_path}")

        voice_file = f"{voice_file_id}.ogg"
        await message.bot.download_file(file_path.file_path, voice_file)
        logging.info(f"Файл сохранён как: {voice_file}")

        # Преобразование голоса в текст
        text = speech_to_text(voice_file)
        logging.info(f"Распознанный текст: {text}")

        await state.update_data(original_text=text)
        await message.reply(
            f"Распознанный текст: {text}\nТеперь выберите язык для перевода (например: 'en', 'pl', 'de').")
        await state.set_state(TranslateStates.waiting_for_language_to_speech)
        logging.info("Установлено состояние: waiting_for_language")
    except Exception as e:
        logging.error(f"Ошибка при обработке голосового сообщения: {str(e)}")
        await message.reply(f"Произошла ошибка при обработке голосового сообщения: {str(e)}")
        await state.clear()


@router.message(TranslateStates.waiting_for_language_to_speech)
async def choose_language_for_audio(message: Message, state: FSMContext):
    selected_language = message.text.strip().lower()
    logging.info(f"Выбран язык: {selected_language}")

    if selected_language not in ['en', 'pl', 'de', 'ru']:
        await message.reply(
            "Некорректный язык. Пожалуйста, выберите допустимый код языка (например: 'en', 'pl', 'de').")
        logging.warning(f"Некорректный выбор языка: {selected_language}")
        return

    data = await state.get_data()
    original_text = data.get('original_text')
    logging.debug(f"Оригинальный текст для перевода: {original_text}")

    try:
        result = translate_text(original_text, to_langs=[selected_language])
        translated_text = result[0]['translations'][0]['text'] if 'translations' in result[0] else None
        logging.info(f"Переведённый текст: {translated_text}")

        if translated_text:
            await state.update_data(translated_text=translated_text, selected_language=selected_language)
            await message.reply(
                f"Переведённый текст: {translated_text}\nТеперь выберите голос: 'male' или 'female' ('male' недоступен для 'pl').")
            await state.set_state(SpeechStates.waiting_for_gender_to_speech)
            logging.info("Установлено состояние: waiting_for_gender")
        else:
            logging.error("Ошибка: перевод текста вернул пустой результат.")
            await message.reply("Ошибка при переводе текста.")
            await state.clear()
    except Exception as e:
        logging.error(f"Ошибка при переводе текста: {str(e)}")
        await message.reply("Ошибка при переводе текста.")
        await state.clear()


@router.message(SpeechStates.waiting_for_gender_to_speech)
async def choose_voice_and_speak(message: Message, state: FSMContext):
    selected_gender = message.text.strip().lower()
    logging.info(f"Выбран голос: {selected_gender}")

    data = await state.get_data()
    selected_language = data.get('selected_language')
    translated_text = data.get('translated_text')
    logging.debug(f"Язык: {selected_language}, Текст для озвучки: {translated_text}")

    if selected_language == 'pl' and selected_gender == 'male':
        await message.reply("Для польского языка доступен только женский голос. Пожалуйста, выберите 'female'.")
        logging.warning("Попытка выбрать мужской голос для польского языка.")
        return
    elif selected_gender not in ['male', 'female']:
        await message.reply("Ошибка: Пожалуйста, выберите 'male' или 'female'.")
        logging.warning(f"Некорректный выбор голоса: {selected_gender}")
        return

    tts = TextToSpeech(
        aws_access_key=os.getenv('aws_access_key'),
        aws_secret_key=os.getenv('aws_secret_key'),
        aws_region_name=os.getenv('AWS_DEFAULT_REGION')
    )

    try:
        output_file = tts.synthesize_speech(text=translated_text, language=selected_language, gender=selected_gender)
        logging.info(f"Озвучка текста выполнена, файл сохранён: {output_file}")

        await message.reply_audio(FSInputFile(output_file), caption="Вот ваша озвучка текста.")
        os.remove(output_file)  # Удаляем временный файл
        logging.debug(f"Удалён временный файл озвучки: {output_file}")
    except Exception as e:
        logging.error(f"Ошибка при озвучке текста: {str(e)}")
        await message.reply(f"Произошла ошибка при озвучке текста: {str(e)}")

    await state.clear()
    logging.info("Состояние очищено.")
