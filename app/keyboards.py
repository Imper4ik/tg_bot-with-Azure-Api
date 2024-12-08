from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

# Создание клавиатуры с командами
commands_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='full commands'), KeyboardButton(text='show your information')],
        [KeyboardButton(text='links'), KeyboardButton(text='help')],
        [KeyboardButton(text='language_interface'), KeyboardButton(text='handle_audio_to_speech')],
        [KeyboardButton(text='Voice_in_text')],
        [KeyboardButton(text='Translate')],
        [KeyboardButton(text='Text_to_Speech')],
    ],
    resize_keyboard=True,  # Уменьшает размер клавиатуры под размер кнопок
    input_field_placeholder='Выберите пункт меню.'  # Место для ввода текста
)

urls = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='YouTube', url='https://www.youtube.com/watch?v=BkxQr9BoOAQ')],
        [InlineKeyboardButton(text='ChatGpt', url='https://chatgpt.com')]
    ]
)
language_interface = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='English', callback_data='language_en')],
        [InlineKeyboardButton(text='Русский', callback_data='language_ru')],
        [InlineKeyboardButton(text='Polski', callback_data='language_pl')],
    ]
)
