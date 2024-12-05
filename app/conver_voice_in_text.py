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
        logging.error("Аудиофайл не найден: %s", voice_file)
        return "Ошибка: Аудиофайл не найден."

    # Определяем имя файла для сохранения в соответствующей папке
    ogg_file = os.path.join(ogg_folder, os.path.basename(voice_file))
    wav_file = os.path.join(wav_folder, os.path.basename(voice_file.replace('.ogg', '.wav')))  # Сохраняем файл в папке Voices/wav

    # Перемещаем файл в папку ogg
    try:
        os.rename(voice_file, ogg_file)
    except Exception as e:
        logging.error("Ошибка при перемещении файла в папку ogg: %s", str(e))
        return "Ошибка при перемещении файла."

    # Конвертация OGG в WAV
    try:
        audio_segment = AudioSegment.from_file(ogg_file, format='ogg')
        audio_segment.export(wav_file, format='wav')
    except Exception as e:
        logging.error("Ошибка при конвертации файла: %s", str(e))
        return "Ошибка при конвертации файла."

    try:
        logging.info("Запуск распознавания речи для файла: %s", wav_file)

        # Создаем конфигурацию для распознавания речи
        speech_config = speechsdk.SpeechConfig(subscription=azure_speech_key, region=azure_region)
        audio_input = speechsdk.AudioConfig(filename=wav_file)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

        # Запускаем распознавание
        result = speech_recognizer.recognize_once()

        # Проверяем результат распознавания
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logging.info("Речь распознана: %s", result.text)
            return result.text
        else:
            logging.error("Ошибка распознавания речи: %s", result.reason)
            if result.reason == speechsdk.ResultReason.Canceled:
                if result.cancellation_details.error_details:  # Проверка наличия error_details
                    logging.error("Подробности ошибки: %s", result.cancellation_details.error_details)
            return "Ошибка распознавания речи"
    except Exception as e:
        logging.exception("Произошла ошибка: %s", str(e))
        return f"Ошибка: {str(e)}"
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
            print(f"Файл {file_path} успешно удален.")
            return True
        except OSError as e:
            if e.errno == 32:  # WinError 32 - файл занят
                print(f"Файл {file_path} занят. Попытка {attempt + 1} из {retries}.")
                time.sleep(delay)
                attempt += 1
            else:
                print(f"Не удалось удалить файл {file_path}: {e}")
                return False
    print(f"Не удалось удалить файл {file_path} после {retries} попыток.")
    return False
