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
    path = '/detect'
    constructed_url = azure_translate_endpoint + path

    params = {
        'api-version': '3.0'
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
        user_language = response.json()[0]['language']  # Вернем код языка
        return user_language
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при определении языка: {e}")
        return None


def translate_text(text, to_langs):
    # Определяем язык текста перед переводом
    from_lang = detect_language(text)

    if not from_lang:
        print("Не удалось определить язык текста.")
        return None

    path = '/translate'
    constructed_url = azure_translate_endpoint + path

    params = {
        'api-version': '3.0',
        'from': from_lang,
        'to': to_langs  # Используем переданный язык перевода
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

        # Получаем результаты перевода
        translations = response.json()

        # Сохраняем переводы в текстовый файл
        with open('translated_text.txt', 'w', encoding='utf-8') as f:
            for translation in translations:
                for trans in translation['translations']:
                    f.write(f"{trans['to']}: {trans['text']}\n")

        return translations  # Возвращаем переводы для дальнейшего использования

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при переводе текста: {e}")
        # Выводим ответ сервера, если доступно
        if e.response is not None:
            print(f"Ответ сервера: {e.response.text}")
        return None
