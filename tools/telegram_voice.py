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
import logging
import queue
import threading
from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable

# Попробуем импортировать telegram, если установлен
try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    # Библиотеки могут отсутствовать в окружении, оставляем заглушки
    Bot = None  # type: ignore


@dataclass
class SpeechKitClient:
    """Minimal client for Yandex SpeechKit REST API."""

    api_key: str

    def stt(self, file_path: str) -> str:
        return stt(file_path, self.api_key)

    def tts(self, text: str) -> bytes:
        return tts(text, self.api_key)


def stt(file_path: str, api_key: str | None = None) -> str:
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


def tts(text: str, api_key: str | None = None) -> bytes:
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
    """Простейший long‑polling бот для приёма текстовых и голосовых сообщений.

    Parameters
    ----------
    token:
        Токен Telegram‑бота.
    forward_callback:
        Опциональная функция, которая принимает текст сообщения и
        возвращает текст ответа. Если не указана, бот будет повторять
        сообщения пользователя (echo).
    """

    def __init__(self, token: str, speechkit: SpeechKitClient, forward_callback: Optional[Callable[[str], Optional[str]]] = None, *, use_webhook: bool = False, webhook_url: str | None = None, listen_port: int = 8000):
        if Bot is None:
            raise RuntimeError(
                "Не установлена библиотека python-telegram-bot. Установите её для работы Telegram‑бота."
            )
        self.token = token
        self.speechkit = speechkit
        self.application = Application.builder().token(token).build()
        self._use_webhook = use_webhook
        self._webhook_url = webhook_url or os.getenv("TG_WEBHOOK_URL")
        self._listen_port = listen_port

        self.updater = Updater(token, use_context=True)
        dispatcher = self.updater.dispatcher

        self.forward_callback = forward_callback
        self._out_queue: "queue.Queue[str]" = queue.Queue()

        # start background thread for sending queued messages
        threading.Thread(target=self._sender_loop, daemon=True).start()

        self._last_chat_id: Optional[int] = None

        dispatcher.add_handler(MessageHandler(Filters.voice, self.handle_voice))
        dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), self.handle_text))

    def handle_voice(self, update: "Update", context: "CallbackContext") -> None:
        """Обработка входящего голосового сообщения."""
        file = update.message.voice.get_file()
        file_path = file.download()
        self._last_chat_id = update.effective_chat.id
        transcript = self.speechkit.stt(file_path)
        if self.forward_callback:
            reply = self.forward_callback(transcript)
        else:
            reply = f"[echo] {transcript}"

        if reply:
            audio = self.speechkit.tts(reply)
            if audio:
                import io

                update.message.reply_voice(voice=io.BytesIO(audio))
            else:
                update.message.reply_text(reply)

    def handle_text(self, update: "Update", context: "CallbackContext") -> None:
        """Обработка входящего текстового сообщения."""
        user_text = update.message.text
        self._last_chat_id = update.effective_chat.id
        if self.forward_callback:
            reply = self.forward_callback(user_text)
        else:
            reply = f"[echo] {user_text}"

        if reply:
            audio = self.speechkit.tts(reply)
            if audio:
                import io

                update.message.reply_voice(voice=io.BytesIO(audio))
            else:
                update.message.reply_text(reply)

    def run(self) -> None:
        """Запустить long-polling или webhook-режим."""

        if self._use_webhook and self._webhook_url:
            # set webhook and start flask-based server inside telegram bot api
            self.updater.bot.set_webhook(url=self._webhook_url)
            self.updater.start_webhook(listen="0.0.0.0", port=self._listen_port, url_path="")
        else:
            self.updater.start_polling()

        self.updater.idle()

    def send_message(self, text: str) -> None:
        """Send a message from MAS to the last active chat."""
        if not self._last_chat_id:
            return
        self._out_queue.put(text)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _sender_loop(self) -> None:
        while True:
            text = self._out_queue.get()
            if not self._last_chat_id:
                continue
            try:
                audio = self.speechkit.tts(text)
                if audio:
                    import io

                    self.bot.send_voice(chat_id=self._last_chat_id, voice=io.BytesIO(audio))
                else:
                    self.bot.send_message(chat_id=self._last_chat_id, text=text)
            except Exception as exc:
                logging.error("[TG] send error: %s", exc)
            self._out_queue.task_done()


def run_telegram_bot(
    token: str,
    speechkit_client: SpeechKitClient,
    forward_callback: Optional[Callable[[str], Optional[str]]] = None,
    *,
    use_webhook: bool = False,
    webhook_url: str | None = None,
    listen_port: int = 8000,
) -> None:
    """Create and run the Telegram voice bot."""

    from .callbacks import register_telegram_sender

    bot = TelegramVoiceBot(token, speechkit_client, forward_callback, use_webhook=use_webhook, webhook_url=webhook_url, listen_port=listen_port)
    register_telegram_sender(bot.send_message)
    bot.run()


if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    ya_key = os.getenv("YA_SPEECHKIT_API_KEY")
    if not token:
        raise RuntimeError("Не указан TELEGRAM_TOKEN в переменных окружения")
    if not ya_key:
        raise RuntimeError("Не указан YA_SPEECHKIT_API_KEY в переменных окружения")
    run_telegram_bot(token, SpeechKitClient(ya_key))
