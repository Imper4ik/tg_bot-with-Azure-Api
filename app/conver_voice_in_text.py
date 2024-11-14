import ffmpeg
import os
import logging
import time
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

# Загрузить переменные окружения из файла .env
load_dotenv()

azure_speech_key = os.getenv('azure_speech_key')
azure_region = os.getenv('azure_region')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


def speech_to_text(voice_file):
    # Проверяем, существует ли файл
    if not os.path.isfile(voice_file):
        logging.error("Аудиофайл не найден: %s", voice_file)
        return "Ошибка: Аудиофайл не найден."

    # Преобразование OGG в WAV с использованием ffmpeg
    wav_file = voice_file.replace('.ogg', '.wav')
    try:
        ffmpeg.input(voice_file).output(wav_file).run()
    except Exception as e:
        logging.error("Ошибка при конвертации файла: %s", str(e))
        return "Ошибка при конвертации файла"

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
            try:
                os.remove(wav_file)
                logging.info("Файл %s успешно удален.", wav_file)
            except Exception as e:
                logging.error("Не удалось удалить файл %s: %s", wav_file, str(e))
                time.sleep(2)  # Ждем перед повторной попыткой
