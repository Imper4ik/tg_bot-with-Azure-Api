from dotenv import load_dotenv

import requests
import uuid
import os


# Загрузить переменные окружения из файла .env
load_dotenv()

# Получаем ключи и URL из переменных окружения
azure_translate_key = os.getenv('azure_translate_key')
azure_translate_region = os.getenv('azure_translate_region')
azure_translate_endpoint = os.getenv('azure_translate_endpoint')


def detect_language(text):
    path = '/translate'
    constructed_url = f"{azure_translate_endpoint.rstrip('/')}{path}"  # Исправленный путь
    print(f"Language definition URL: {constructed_url}")  # Для отладки

    params = {'api-version': '3.0', 'to': 'en'}  # Перевод на английский как способ получить язык
    headers = {
        'Ocp-Apim-Subscription-Key': azure_translate_key,
        'Ocp-Apim-Subscription-Region': azure_translate_region,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{'text': text}]

    try:
        response = requests.post(constructed_url, params=params, headers=headers, json=body)
        response.raise_for_status()
        translations = response.json()

        # Определяем язык из ответа API
        detected_language = translations[0]['detectedLanguage']['language']
        print(f"Specific language: {detected_language}")  # Для отладки
        return detected_language
    except requests.exceptions.RequestException as e:
        print(f"Error when detecting language: {e}")
        if e.response is not None:
            print(f"Server response: {e.response.text}")  # Отладочная информация
        return None


def translate_text(text, to_langs):
    # Определяем язык текста перед переводом
    from_lang = detect_language(text)

    if not from_lang:
        print("The language of the text could not be determined.")
        return None

    path = '/translate'
    constructed_url = f"{azure_translate_endpoint.rstrip('/')}{path}"  # Формируем полный URL
    print(f"URL for translation: {constructed_url}")  # Отладка

    params = {
        'api-version': '3.0',
        'from': from_lang,
        'to': to_langs
    }

    headers = {
        'Ocp-Apim-Subscription-Key': azure_translate_key,
        'Ocp-Apim-Subscription-Region': azure_translate_region,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{'text': text}]

    try:
        response = requests.post(constructed_url, params=params, headers=headers, json=body)
        response.raise_for_status()
        print(f"API translate_text response: {response.json()}")  # Отладка
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error translating text: {e}")
        if e.response is not None:
            print(f"Server response: {e.response.text}")  # Отладка
        return None
