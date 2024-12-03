import logging
import os
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError


class TextToSpeech:
    def __init__(self, aws_access_key: str, aws_secret_key: str, aws_region_name: str, voice_id: str = "Joanna"):
        """
        Инициализация клиента AWS Polly.
        """
        self.session = Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region_name
        )
        self.polly = self.session.client("polly")
        self.voice_id = voice_id

    def synthesize_speech(self, text: str, output_file: str = "speech.mp3") -> str:
        """
        Генерация речи из текста и сохранение в аудиофайл.
        :param text: Текст для озвучивания.
        :param output_file: Путь для сохранения MP3-файла.
        :return: Путь к сгенерированному файлу.
        """
        try:
            response = self.polly.synthesize_speech(
                Text=text,
                OutputFormat="mp3",
                VoiceId=self.voice_id
            )

            with open(output_file, "wb") as file:
                file.write(response["AudioStream"].read())

            return output_file

        except (BotoCoreError, ClientError) as error:
            logging.error(f"Ошибка AWS Polly: {error}")
            raise RuntimeError("Ошибка при генерации речи.")