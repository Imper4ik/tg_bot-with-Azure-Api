from pydub import AudioSegment
from dotenv import load_dotenv
import time
import azure.cognitiveservices.speech as speechsdk
import logging
import os


# Загрузить переменные окружения из файла .env
load_dotenv()

azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
azure_region = os.getenv("AZURE_REGION")


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Папка для сохранения файлов
voices_folder = "Voices"
ogg_folder = os.path.join(voices_folder, "ogg")
wav_folder = os.path.join(voices_folder, "wav")

# Создаем папки, если их нет
os.makedirs(ogg_folder, exist_ok=True)
os.makedirs(wav_folder, exist_ok=True)


def speech_to_text(voice_file):
    # Проверяем, существует ли файл
    if not os.path.isfile(voice_file):
        logging.error("Audio file not found: %s", voice_file)
        return "ERROR: Audio file not found:"

    # Определяем имя файла для сохранения в соответствующей папке
    ogg_file = os.path.join(ogg_folder, os.path.basename(voice_file))
    wav_file = os.path.join(wav_folder, os.path.basename(voice_file.replace('.ogg', '.wav')))

    # Перемещаем файл в папку ogg
    try:
        os.rename(voice_file, ogg_file)
    except Exception as e:
        logging.error("Error while moving the file to the ogg folder: %s", str(e))
        return "Error while moving the file."

    # Конвертация OGG в WAV
    try:
        audio_segment = AudioSegment.from_file(ogg_file, format='ogg')
        audio_segment.export(wav_file, format='wav')
    except Exception as e:
        logging.error("Error while converting the file: %s", str(e))
        return "Error while converting the file."

    try:
        logging.info("Start speech for a file: %s", wav_file)

        # Создаем конфигурацию для распознавания речи
        speech_config = speechsdk.SpeechConfig(subscription=azure_speech_key, region=azure_region)
        audio_input = speechsdk.AudioConfig(filename=wav_file)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

        # Запускаем распознавание
        result = speech_recognizer.recognize_once()

        # Проверяем результат распознавания
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logging.info("Speech recognized: %s", result.text)
            return result.text
        else:
            logging.error("Speech recognition error: %s", result.reason)
            if result.reason == speechsdk.ResultReason.Canceled:
                if result.cancellation_details.error_details:  # Проверка наличия error_details
                    logging.error("Error details: %s", result.cancellation_details.error_details)
            return "Speech recognition error"
    except Exception as e:
        logging.exception("An error occurred: %s", str(e))
        return f"Error: {str(e)}"
    finally:
        # Завершаем работу распознавателя
        if 'speech_recognizer' in locals():
            speech_recognizer.stop_continuous_recognition()

        # Удаляем временные файлы с задержкой
        if os.path.isfile(wav_file):
            time.sleep(1)  # Увеличенная задержка перед удалением
            remove_file_with_retry(wav_file)
        if os.path.isfile(ogg_file):
            time.sleep(1)  # Увеличенная задержка перед удалением
            remove_file_with_retry(ogg_file)


# Функция для удаления файла с повторной попыткой
def remove_file_with_retry(file_path, retries=5, delay=2):
    attempt = 0
    while attempt < retries:
        try:
            os.remove(file_path)
            print(f"File {file_path} was successfully deleted.")
            return True
        except OSError as e:
            if e.errno == 32:  # WinError 32 - файл занят
                print(f"File {file_path} is busy. Trying {attempt + 1} from {retries}.")
                time.sleep(delay)
                attempt += 1
            else:
                print(f"Failed to delete file {file_path}: {e}")
                return False
    print(f"Failed to delete file {file_path} after {retries} attempts.")
    return False
