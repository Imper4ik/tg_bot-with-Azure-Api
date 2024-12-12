import time
import app.keyboards as kb
import os
import logging

from aiogram import F, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from dotenv import load_dotenv
from app.conver_voice_in_text import speech_to_text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from app.text_into_speech import TextToSpeech
from app.translate_text import translate_text


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
MAX_MESSAGES_PER_MINUTE = 30
TIME_FRAME = 60  # 60 секунд


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


# Функция для проверки, не превышен ли лимит сообщений
def is_user_spamming(user_id: int) -> bool:
    current_time = time.time()

    if user_id not in user_message_times:
        user_message_times[user_id] = []

    # Очищаем старые записи сообщений (более 1 минуты назад)
    user_message_times[user_id] = [
        timestamp for timestamp in user_message_times[user_id] if current_time - timestamp < TIME_FRAME
    ]

    # Проверяем, не превышено ли количество сообщений
    if len(user_message_times[user_id]) >= MAX_MESSAGES_PER_MINUTE:
        return True

    # Добавляем временную метку нового сообщения
    user_message_times[user_id].append(current_time)
    return False


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer('Full commands: \n '
                         '1 - Full commands \n'
                         '2 - Show your information \n'
                         '3 - Help \n'
                         '4 - Convert voice to text \n'
                         '5 - Translation of text \n'
                         '6 - Convert text to voice \n'
                         '7 - Voice translation and dubbing', reply_markup=kb.commands_keyboard)


@router.message(F.text)
async def handle_text_commands(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Проверяем, не превышен ли лимит сообщений
    if is_user_spamming(user_id):
        await message.reply("You are sending too many messages. Please wait a bit.")
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
        if message.text == 'Full commands':
            await cmd_start(message)
        elif message.text == 'Show your information':
            await show(message)
        elif message.text == 'Help':
            await get_help(message)
        elif message.text == 'Convert voice to text':
            await request_and_handle_voice_message(message)
        elif message.text == 'Translation of text':
            await start_translate(message, state)
        elif message.text == 'Convert text to voice':
            await request_language_for_speech(message, state)
        elif message.text == 'Voice translation and dubbing':
            await handle_audio_to_speech(message, state)
        else:
            await message.reply("Unknown command. Please select an option from the menu.")


@router.message(Command('show'))
async def show(message: Message):
    await message.reply(f'Hello, your ID: {message.from_user.id}\nName: {message.from_user.first_name}')


@router.message(Command('help'))
async def get_help(message: types.Message):
    await message.answer("Link to the developer's Telegram: @Mando_Grogu")


# Обработчик команды /Voice_in_text
@router.message(Command('Voice_in_text'))
async def request_and_handle_voice_message(message: Message):
    await message.reply('Start recording a voice message.(only Eng)')

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
    await message.reply("Please select the language you want to translate to (e.g., 'en', 'pl', 'de').")
    await state.set_state(TranslateStates.waiting_for_language)


# Ожидание ввода языка для перевода
@router.message(TranslateStates.waiting_for_language)
async def choose_language(message: types.Message, state: FSMContext):
    selected_language = message.text.strip().lower()
    # Проверка правильности введенного языка (можете добавить дополнительные проверки)
    if selected_language:
        await state.update_data(selected_language=selected_language)
        await message.reply("Now, please enter the text to translate.")
        await state.set_state(TranslateStates.waiting_for_text)
    else:
        await message.reply("Invalid language. Please enter a valid language code (e.g., 'en', 'pl', 'de').")


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
            await message.reply("Translation not found.")
        else:
            await message.reply("\n".join(translations))
    else:
        await message.reply("Error while translating the text.")

    await state.clear()


# Озвучка текста
@router.message(Command('Text_to_Speech'))
async def request_language_for_speech(message: Message, state: FSMContext):
    # Запрашиваем у пользователя язык для озвучивания
    await message.reply("Select the voiceover language ('en', 'ru', 'pl', 'de').")
    await state.set_state(SpeechStates.waiting_for_language)


@router.message(SpeechStates.waiting_for_language)
async def handle_language_selection(message: types.Message, state: FSMContext):
    selected_language = message.text.strip().lower()
    if selected_language not in TextToSpeech.VOICE_MAP:
        await message.reply("Unsupported language. Please choose from 'en', 'ru', 'pl', 'de'.")
        return

    await state.update_data(language=selected_language)
    await message.reply("Now, choose a voice: 'male' or 'female' ('male' is unavailable for 'pl').")
    await state.set_state(SpeechStates.waiting_for_gender)


@router.message(SpeechStates.waiting_for_gender)
async def handle_gender_selection(message: types.Message, state: FSMContext):
    selected_gender = message.text.strip().lower()
    data = await state.get_data()
    selected_language = data.get("language")

    # Проверка на допустимость выбранного пола для языка
    if selected_language == 'pl' and selected_gender == 'male':
        await message.reply("Only the female voice is available for Polish. Please select 'female'.")
        return
    elif selected_gender not in ['male', 'female']:
        await message.reply("Error: Please choose 'male' or 'female'. Try again.")
        return  # Ожидаем новый ввод от пользователя

    # Сохраняем данные языка и пола
    await state.update_data(language=selected_language, gender=selected_gender)

    # Переходим к следующему шагу
    await message.reply("Now, please enter the text you want to convert to speech.\n")
    await state.set_state(SpeechStates.waiting_for_speech_text)


@router.message(SpeechStates.waiting_for_speech_text)
async def handle_text_to_speech(message: types.Message, state: FSMContext):
    data = await state.get_data()
    language = data.get("language")
    gender = data.get("gender")
    text_to_speech = message.text

    if len(text_to_speech) > 3000:
        await message.reply("The text is too long. Please enter text up to 3000 characters.")
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
        await message.reply_audio(FSInputFile(output_file), caption="Here is your text-to-speech.")

        # Удаляем временный файл после отправки
        os.remove(output_file)
    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}.")

    await state.clear()


@router.message(Command('handle_audio_to_speech'))
async def handle_audio_to_speech(message: Message, state: FSMContext):
    logging.info(f"The command /handle_audio_to_speech was received from the user. {message.from_user.id}")
    await message.reply("Please record a voice message (Eng).")
    await state.set_state(SpeechStates.waiting_for_audio)
    logging.info("The status is set to: waiting_for_audio.")


@router.message(SpeechStates.waiting_for_audio)
async def process_audio(message: Message, state: FSMContext):
    try:
        logging.info(f"A voice message has been received from the user. {message.from_user.id}")
        voice_file_id = message.voice.file_id
        logging.debug(f"Voice file ID: {voice_file_id}")

        file_path = await message.bot.get_file(voice_file_id)
        logging.info(f"The file path has been received: {file_path.file_path}")

        voice_file = f"{voice_file_id}.ogg"
        await message.bot.download_file(file_path.file_path, voice_file)
        logging.info(f"The file has been saved as: {voice_file}")

        # Преобразование голоса в текст
        text = speech_to_text(voice_file)
        logging.info(f"Recognized text: {text}")

        await state.update_data(original_text=text)
        await message.reply(
            f"Recognized text: {text}\n\nNow, please select the language for translation (e.g., 'en', 'pl', 'de').")
        await state.set_state(TranslateStates.waiting_for_language_to_speech)
        logging.info("The status is set to: waiting_for_language.")
    except Exception as e:
        logging.error(f"Error while processing the voice message: {str(e)}")
        await message.reply(f"An error occurred while processing the voice message: {str(e)}")
        await state.clear()


@router.message(TranslateStates.waiting_for_language_to_speech)
async def choose_language_for_audio(message: Message, state: FSMContext):
    selected_language = message.text.strip().lower()
    logging.info(f"Selected language: {selected_language}")

    if selected_language not in ['en', 'pl', 'de', 'ru']:
        await message.reply(
            "Invalid language. Please select a valid language code (e.g., 'en', 'pl', 'de').")
        logging.warning(f"Invalid language selection: {selected_language}")
        return

    data = await state.get_data()
    original_text = data.get('original_text')
    logging.debug(f"Original text for translation: {original_text}")

    try:
        result = translate_text(original_text, to_langs=[selected_language])
        translated_text = result[0]['translations'][0]['text'] if 'translations' in result[0] else None
        logging.info(f"Translated text: {translated_text}")

        if translated_text:
            await state.update_data(translated_text=translated_text, selected_language=selected_language)
            await message.reply(
                f"Translated text: {translated_text}\n\n"
                f"Now, please select a voice: 'male' or 'female' ('male' is unavailable for 'pl').")
            await state.set_state(SpeechStates.waiting_for_gender_to_speech)
            logging.info("The status is set to: waiting_for_gender.")
        else:
            logging.error("Error: the translation returned an empty result.")
            await message.reply("Error while translating the text.")
            await state.clear()
    except Exception as e:
        logging.error(f"Error while translating the text: {str(e)}.")
        await message.reply("Error while translating the text.")
        await state.clear()


@router.message(SpeechStates.waiting_for_gender_to_speech)
async def choose_voice_and_speak(message: Message, state: FSMContext):
    selected_gender = message.text.strip().lower()
    logging.info(f"Selected voice: {selected_gender}")

    data = await state.get_data()
    selected_language = data.get('selected_language')
    translated_text = data.get('translated_text')
    logging.debug(f"Language: {selected_language}, Text to be voiced: {translated_text}")

    if selected_language == 'pl' and selected_gender == 'male':
        await message.reply("For Polish, only the female voice is available. Please select 'female'.")
        logging.warning("Attempt to select a male voice for Polish language.")
        return
    elif selected_gender not in ['male', 'female']:
        await message.reply("Error: Please select 'male' or 'female'.")
        logging.warning(f"Invalid voice selection: {selected_gender}")
        return

    tts = TextToSpeech(
        aws_access_key=os.getenv('aws_access_key'),
        aws_secret_key=os.getenv('aws_secret_key'),
        aws_region_name=os.getenv('AWS_DEFAULT_REGION')
    )

    try:
        output_file = tts.synthesize_speech(text=translated_text, language=selected_language, gender=selected_gender)
        logging.info(f"Text-to-speech completed, the file has been saved: {output_file}")

        await message.reply_audio(FSInputFile(output_file), caption="Here is your text-to-speech.")
        os.remove(output_file)  # Удаляем временный файл
        logging.debug(f"The temporary text-to-speech file has been deleted: {output_file}")
    except Exception as e:
        logging.error(f"Error while converting text to speech: {str(e)}")
        await message.reply(f"An error occurred while converting text to speech: {str(e)}")

    await state.clear()
    logging.info("The state has been cleared.")
