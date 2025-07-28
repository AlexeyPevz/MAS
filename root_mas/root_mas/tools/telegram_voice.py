"""
telegram_voice.py
===================

Заготовка для Telegram‑бота с поддержкой STT (speech‑to‑text) и TTS (text‑to‑speech)
через сервис Яндекс SpeechKit. Этот скрипт реализует long‑polling бота,
получает сообщения от пользователя, преобразует голосовые сообщения в текст и
отправляет текстовые ответы пользователю. Для работы требуются ключи API,
которые следует указать в файле `.env` или передать через переменные окружения.

Реальная реализация должна использовать библиотеки `python‑telegram‑bot`
или аналогичные, а также SDK для Яндекс SpeechKit. Здесь представлены
заглушки для интерфейса.
"""

import os
from typing import Optional, Dict, Any
import logging

# Попробуем импортировать telegram, если установлен
try:
    from telegram import Update, Bot
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
except ImportError:
    # Библиотеки могут отсутствовать в окружении, оставляем заглушки
    Bot = None  # type: ignore


class SpeechKitClient:
    """Мини‑клиент Yandex SpeechKit для STT и TTS."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def stt(self, file_path: str) -> str:
        return stt(file_path, api_key=self.api_key)

    def tts(self, text: str) -> bytes:
        return tts(text, api_key=self.api_key)


def stt(file_path: str, api_key: Optional[str] = None) -> str:
    """Преобразовать голосовой файл (OGG) в текст с помощью Yandex SpeechKit.

    Args:
        file_path: путь к аудиофайлу в формате OGG

    Returns:
        Распознанный текст или пустая строка при ошибке.
    """
    try:
        import requests  # type: ignore
    except ImportError:
        raise RuntimeError("Для работы STT требуется библиотека requests. Установите её: pip install requests")

    yandex_api_key = api_key or os.getenv("YA_SPEECHKIT_API_KEY")
    if not yandex_api_key:
        logging.error("Не указан YA_SPEECHKIT_API_KEY в .env")
        return ""

    # Получить IAM‑токен (в production необходимо реализовать refresh)
    iam_token = yandex_api_key
    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    params = {
        "lang": "ru-RU",
    }
    headers = {
        "Authorization": f"Api-Key {iam_token}",
    }
    with open(file_path, "rb") as f:
        data = f.read()
    response = requests.post(url, params=params, headers=headers, data=data)
    if response.status_code != 200:
        logging.error(f"SpeechKit STT error: {response.text}")
        return ""
    result = response.json()
    return result.get("result", "")


def tts(text: str, api_key: Optional[str] = None) -> bytes:
    """Сгенерировать голосовой ответ из текста через Yandex SpeechKit.

    Args:
        text: текст для озвучивания

    Returns:
        Байты аудиофайла в формате OGG. При ошибке возвращается пустой байтовый объект.
    """
    try:
        import requests  # type: ignore
    except ImportError:
        raise RuntimeError("Для работы TTS требуется библиотека requests. Установите её: pip install requests")

    yandex_api_key = api_key or os.getenv("YA_SPEECHKIT_API_KEY")
    if not yandex_api_key:
        logging.error("Не указан YA_SPEECHKIT_API_KEY в .env")
        return b""

    iam_token = yandex_api_key
    url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
    data: Dict[str, Any] = {
        "text": text,
        "lang": "ru-RU",
        "voice": "alena",
        "format": "oggopus",
    }
    headers = {
        "Authorization": f"Api-Key {iam_token}",
    }
    response = requests.post(url, data=data, headers=headers)
    if response.status_code != 200:
        logging.error(f"SpeechKit TTS error: {response.text}")
        return b""
    return response.content


class TelegramVoiceBot:
    """Простейший long‑polling бот для приёма текстовых и голосовых сообщений."""

    def __init__(self, token: str, speechkit_client: Optional[SpeechKitClient] = None):
        if Bot is None:
            raise RuntimeError(
                "Не установлена библиотека python-telegram-bot. Установите её для работы Telegram‑бота."
            )
        self.token = token
        self.speechkit = speechkit_client or SpeechKitClient(os.getenv("YA_SPEECHKIT_API_KEY", ""))
        self.bot = Bot(token=token)
        self.updater = Updater(token, use_context=True)
        dispatcher = self.updater.dispatcher

        dispatcher.add_handler(MessageHandler(Filters.voice, self.handle_voice))
        dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), self.handle_text))
        # Импортируем callback для отправки сообщений пользователю.
        try:
            from .callbacks import outgoing_to_telegram  # noqa: F401
        except Exception:
            # Callback может отсутствовать на этапе разработки
            outgoing_to_telegram = None  # type: ignore

    def handle_voice(self, update: "Update", context: "CallbackContext") -> None:
        """Обработка входящего голосового сообщения."""
        file = update.message.voice.get_file()
        file_path = file.download()
        transcript = self.speechkit.stt(file_path)
        # Отправляем текст транскрипции обратно или передаём в Root GroupChat
        # Здесь можно вызвать Root GroupChat, а затем отправить результат
        update.message.reply_text(transcript)

    def handle_text(self, update: "Update", context: "CallbackContext") -> None:
        """Обработка входящего текстового сообщения."""
        user_text = update.message.text
        # TODO: отправить текст в Root GroupChat и получить ответ
        # Здесь должен быть вызов Root GroupChat через агента Communicator.
        # Пока просто эхо для демонстрации.
        reply = f"[echo] {user_text}"
        update.message.reply_text(reply)

    def run(self) -> None:
        """Запустить цикл long‑polling."""
        self.updater.start_polling()
        self.updater.idle()


def run_telegram_bot(token: str, speechkit_client: Optional[SpeechKitClient] = None) -> None:
    """Упрощённый запуск Telegram‑бота."""
    bot = TelegramVoiceBot(token, speechkit_client=speechkit_client)
    bot.run()


if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    key = os.getenv("YA_SPEECHKIT_API_KEY", "")
    if not token:
        raise RuntimeError("Не указан TELEGRAM_TOKEN в переменных окружения")
    client = SpeechKitClient(api_key=key)
    run_telegram_bot(token, speechkit_client=client)