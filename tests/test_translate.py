from app.translate_text import detect_language, translate_text


def test_detect_language_ru():
    text = 'Привет'
    to_langs = detect_language(text)
    assert to_langs == 'ru'


def test_detect_language_en():
    text = 'hello'
    to_langs = detect_language(text)
    assert to_langs == 'en'


def test_translate_text_ru():
    text = 'hello'
    to_langs = 'ru'
    translated_text = translate_text(text, to_langs)

    # Извлекаем перевод из словаря
    word = translated_text
    word = word[0]['translations'][0]['text'].lower()
    assert word == 'привет'


def test_translate_text_eng():
    text = 'привет'
    to_langs = 'en'
    translated_text = translate_text(text, to_langs)

    # Извлекаем перевод из словаря
    word = translated_text
    word = word[0]['translations'][0]['text'].lower()
    assert word == 'hello'
