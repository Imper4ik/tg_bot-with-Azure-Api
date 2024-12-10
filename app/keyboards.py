from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Создание клавиатуры с командами
commands_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='full commands'), KeyboardButton(text='show your information')],
        [KeyboardButton(text='help')],
        [KeyboardButton(text='Voice_in_text')],
        [KeyboardButton(text='Translate')],
        [KeyboardButton(text='Text_to_Speech')],
        [KeyboardButton(text='handle_audio_to_speech')],
    ],
    resize_keyboard=True,  # Уменьшает размер клавиатуры под размер кнопок
    input_field_placeholder='Please select an option from the menu.'  # Место для ввода текста
)
