import requests
import uuid
import json
from config import azure_translate_key, azure_translate_region, azure_translate_endpoint


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
        print(f"Ошибка: {e}")
        return None


def translate_text(text, to_langs=['pl']):
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

        # Получаем результаты перевода
        translations = response.json()

        # Сохраняем переводы в текстовый файл
        with open('translated_text.txt', 'a', encoding='utf-8') as f:  # 'a' для добавления в файл
            for translation in translations:
                # Записываем переводы в файл
                for trans in translation['translations']:
                    f.write(f"{trans['to']}: {trans['text']}\n")

        return translations  # Возвращаем переводы для дальнейшего использования

    except requests.exceptions.RequestException as e:
        print(f"Ошибка: {e}")
        return None
