from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

# Создание клавиатуры с командами
commands_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='start'), KeyboardButton(text='show')],
        [KeyboardButton(text='links'), KeyboardButton(text='help')],
        [KeyboardButton(text='Voice_in_text')],
        [KeyboardButton(text='Translate')]
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

