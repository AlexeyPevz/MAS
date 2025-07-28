"""Telegram bot integration using Yandex SpeechKit for voice features."""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict

try:
    from telegram import Update, Bot
    from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
except Exception:  # pragma: no cover - optional dependency
    Bot = None  # type: ignore

import requests

logger = logging.getLogger(__name__)


@dataclass
class SpeechKitClient:
    api_key: str

    def stt(self, audio_bytes: bytes) -> str:
        """Convert speech to text via Yandex SpeechKit."""
        url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        headers = {"Authorization": f"Api-Key {self.api_key}"}
        params = {"lang": "ru-RU"}
        resp = requests.post(url, headers=headers, params=params, data=audio_bytes)
        if resp.status_code != 200:
            logger.error("SpeechKit STT error: %s", resp.text)
            return ""
        return resp.json().get("result", "")

    def tts(self, text: str) -> bytes:
        """Synthesize speech via Yandex SpeechKit."""
        url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
        headers = {"Authorization": f"Api-Key {self.api_key}"}
        data: Dict[str, Any] = {"text": text, "lang": "ru-RU", "voice": "alena", "format": "oggopus"}
        resp = requests.post(url, headers=headers, data=data)
        if resp.status_code != 200:
            logger.error("SpeechKit TTS error: %s", resp.text)
            return b""
        return resp.content


def run_telegram_bot(token: str, speechkit_client: SpeechKitClient) -> None:
    """Run a simple long polling Telegram bot."""
    if Bot is None:
        raise RuntimeError("python-telegram-bot is required for Telegram bot")

    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher

    def handle_voice(update: Update, context: CallbackContext) -> None:
        file = update.message.voice.get_file()
        path = file.download()
        with open(path, "rb") as f:
            text = speechkit_client.stt(f.read())
        update.message.reply_text(text)

    def handle_text(update: Update, context: CallbackContext) -> None:
        reply_audio = speechkit_client.tts(update.message.text)
        if reply_audio:
            update.message.reply_voice(reply_audio)
        else:
            update.message.reply_text(update.message.text)

    dispatcher.add_handler(MessageHandler(Filters.voice, handle_voice))
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), handle_text))

    logger.info("Starting Telegram bot")
    updater.start_polling()
    updater.idle()
