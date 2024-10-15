from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

# Создание клавиатуры с командами
commands_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='1 - /start')],
        [KeyboardButton(text='2 - /show')],
        [KeyboardButton(text='3 - /url')],
        [KeyboardButton(text='4 - /help')],
        [KeyboardButton(text='5 - /Voice_in_text')],
        [KeyboardButton(text='6 - /Translate')],
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

