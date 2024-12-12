import logging
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError


class TextToSpeech:
    # Словарь голосов для поддерживаемых языков
    VOICE_MAP = {
        'en': {'male': 'Matthew', 'female': 'Joanna'},
        'ru': {'male': 'Maxim', 'female': 'Tatyana'},
        'pl': {'male': 'Mariusz', 'female': 'Ewa'},
        'de': {'male': 'Hans', 'female': 'Marlene'}
    }

    def __init__(self, aws_access_key: str, aws_secret_key: str, aws_region_name: str):
        """
        Инициализация клиента AWS Polly.
        """
        self.session = Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region_name
        )
        self.polly = self.session.client("polly")

    def synthesize_speech(self, text: str, language: str, gender: str, output_file: str = "speech.mp3") -> str:
        """
        Генерация речи из текста и сохранение в аудиофайл.
        :param text: Текст для озвучивания.
        :param language: Код языка (например, 'en', 'ru').
        :param gender: Пол ('male' или 'female').
        :param output_file: Путь для сохранения MP3-файла.
        :return: Путь к сгенерированному файлу.
        """
        if language not in self.VOICE_MAP or gender not in self.VOICE_MAP[language]:
            raise ValueError(f"Unsupported language ({language}) or gender ({gender}).")

        voice_id = self.VOICE_MAP[language][gender]

        try:
            response = self.polly.synthesize_speech(
                Text=text,
                OutputFormat="mp3",
                VoiceId=voice_id
            )

            with open(output_file, "wb") as file:
                file.write(response["AudioStream"].read())

            return output_file

        except (BotoCoreError, ClientError) as error:
            logging.error(f"AWS Polly error: {error}")
            raise RuntimeError("Error when generating speech.")
