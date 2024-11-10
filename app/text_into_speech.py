import requests
import uuid
import os
from dotenv import load_dotenv

# Загрузить переменные окружения из файла .env
load_dotenv()

# Получаем ключи и URL из переменных окружения
azure_translate_key = os.getenv('azure_translate_key')
azure_translate_region = os.getenv('azure_translate_region')
azure_tts_endpoint = "https://westeurope.tts.speech.microsoft.com/cognitiveservices/v1"


class TextToSpeech:
    def __init__(self, language="en-US", voice="en-US-JessaNeural"):
        self.language = language
        self.voice = voice

    def synthesize_speech(self, text: str) -> str:
        """
        Преобразует текст в аудио с помощью Azure Text-to-Speech и возвращает путь к аудиофайлу.

        :param text: Текст для озвучивания
        :return: Путь к сохранённому аудиофайлу
        """
        headers = {
            'Ocp-Apim-Subscription-Key': azure_translate_key,
            'Ocp-Apim-Subscription-Region': azure_translate_region,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'riff-24khz-16bit-mono-pcm',
        }

        # Создаем SSML (Speech Synthesis Markup Language) для настройки озвучки
        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{self.language}'>
            <voice name='{self.voice}'>
                {text}
            </voice>
        </speak>
        """

        try:
            # Делаем запрос к Azure Text-to-Speech API
            response = requests.post(azure_tts_endpoint, headers=headers, data=ssml.encode('utf-8'))
            response.raise_for_status()

            # Сохраняем аудио файл
            audio_filename = "translated_audio.wav"
            with open(audio_filename, "wb") as audio_file:
                audio_file.write(response.content)

            return audio_filename

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при создании аудио: {e}")
            if e.response is not None:
                print(f"Ответ сервера: {e.response.text}")
            return None
