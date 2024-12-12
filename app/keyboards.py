from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Создание клавиатуры с командами
commands_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Full commands'), KeyboardButton(text='Show your information')],
        [KeyboardButton(text='Help')],
        [KeyboardButton(text='Convert voice to text')],
        [KeyboardButton(text='Translation of text')],
        [KeyboardButton(text='Convert text to voice')],
        [KeyboardButton(text='Voice translation and dubbing')],
    ],
    resize_keyboard=True,  # Уменьшает размер клавиатуры под размер кнопок
    input_field_placeholder='Please select an option from the menu.'  # Место для ввода текста
)
