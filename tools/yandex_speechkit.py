"""
Yandex SpeechKit Integration
Интеграция с Yandex SpeechKit для STT и TTS
"""

import os
import asyncio
import aiohttp
import base64
import logging
from typing import Optional, Union
from pathlib import Path


logger = logging.getLogger(__name__)


class YandexSpeechKit:
    """Интеграция с Yandex SpeechKit"""
    
    def __init__(self):
        self.api_key = os.getenv('YANDEX_API_KEY')
        self.folder_id = os.getenv('YANDEX_FOLDER_ID')
        
        # URLs для API
        self.stt_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        self.tts_url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
        
        if not self.api_key or not self.folder_id:
            logger.info("ℹ️ Yandex SpeechKit не настроен. Для включения голосовых функций добавьте YANDEX_API_KEY и YANDEX_FOLDER_ID в .env")
    
    async def speech_to_text(
        self, 
        audio_data: bytes, 
        language: str = "ru-RU",
        format: str = "oggopus"
    ) -> Optional[str]:
        """
        Распознавание речи в текст
        
        Args:
            audio_data: Аудио данные в байтах
            language: Язык распознавания (ru-RU, en-US, etc.)
            format: Формат аудио (oggopus, lpcm, mp3)
        
        Returns:
            Распознанный текст или None при ошибке
        """
        if not self.api_key:
            logger.error("❌ Yandex API Key не настроен")
            return None
        
        try:
            headers = {
                'Authorization': f'Api-Key {self.api_key}',
            }
            
            data = {
                'config': {
                    'specification': {
                        'languageCode': language,
                        'model': 'general',
                        'profanityFilter': False,
                        'literature_text': False,
                        'audioFormat': format,
                        'sampleRateHertz': 48000,
                    }
                },
                'audio': {
                    'content': base64.b64encode(audio_data).decode('utf-8')
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.stt_url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # Извлекаем текст из ответа
                        if 'result' in result and 'chunks' in result['result']:
                            chunks = result['result']['chunks']
                            if chunks and 'alternatives' in chunks[0]:
                                alternatives = chunks[0]['alternatives']
                                if alternatives and 'text' in alternatives[0]:
                                    text = alternatives[0]['text']
                                    logger.info(f"🎤 Распознано: {text}")
                                    return text
                        
                        logger.warning("⚠️ Пустой результат распознавания")
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ SpeechKit STT error {response.status}: {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("❌ Timeout при распознавании речи")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка распознавания речи: {e}")
            return None
    
    async def text_to_speech(
        self, 
        text: str, 
        voice: str = "alena",
        language: str = "ru-RU",
        format: str = "oggopus"
    ) -> Optional[bytes]:
        """
        Синтез речи из текста
        
        Args:
            text: Текст для озвучивания
            voice: Голос (alena, jane, oksana, omazh, zahar, ermil)
            language: Язык (ru-RU, en-US, etc.)
            format: Формат аудио (oggopus, lpcm, mp3)
        
        Returns:
            Аудио данные в байтах или None при ошибке
        """
        if not self.api_key:
            logger.error("❌ Yandex API Key не настроен")
            return None
        
        try:
            headers = {
                'Authorization': f'Api-Key {self.api_key}',
            }
            
            data = {
                'text': text,
                'lang': language,
                'voice': voice,
                'format': format,
                'sampleRateHertz': 48000,
                'folderId': self.folder_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.tts_url,
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        audio_data = await response.read()
                        logger.info(f"🔊 Синтезирован голос для: {text[:50]}...")
                        return audio_data
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ SpeechKit TTS error {response.status}: {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("❌ Timeout при синтезе речи")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка синтеза речи: {e}")
            return None
    
    async def save_audio_file(self, audio_data: bytes, filename: str) -> bool:
        """Сохранение аудио в файл"""
        try:
            # Создаем директорию если не существует
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filename, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"💾 Аудио сохранено: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения аудио: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Проверка настройки SpeechKit"""
        return bool(self.api_key and self.folder_id)


# Глобальный экземпляр
speechkit = YandexSpeechKit()


# Вспомогательные функции для Telegram бота
async def process_voice_message(audio_data: bytes) -> Optional[str]:
    """Обработка голосового сообщения из Telegram"""
    if not speechkit.is_configured():
        return "🔧 SpeechKit не настроен"
    
    try:
        # Распознаем речь
        text = await speechkit.speech_to_text(audio_data, format="ogg")
        
        if text:
            return text
        else:
            return "🤷‍♂️ Не удалось распознать речь"
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки голосового сообщения: {e}")
        return f"❌ Ошибка: {str(e)}"


async def synthesize_response(text: str) -> Optional[bytes]:
    """Синтез голосового ответа"""
    if not speechkit.is_configured():
        return None
    
    try:
        audio_data = await speechkit.text_to_speech(text)
        return audio_data
        
    except Exception as e:
        logger.error(f"❌ Ошибка синтеза ответа: {e}")
        return None


# Тестовая функция
async def test_speechkit():
    """Тест SpeechKit"""
    print("🧪 Тестируем Yandex SpeechKit...")
    
    if not speechkit.is_configured():
        print("❌ SpeechKit не настроен")
        print("Установите переменные окружения:")
        print("export YANDEX_API_KEY='your-api-key'")
        print("export YANDEX_FOLDER_ID='your-folder-id'")
        return
    
    # Тест TTS
    print("🔊 Тестируем синтез речи...")
    audio_data = await speechkit.text_to_speech("Привет! Это тест голосового синтеза.")
    
    if audio_data:
        print(f"✅ TTS работает! Размер аудио: {len(audio_data)} байт")
        await speechkit.save_audio_file(audio_data, "test_output.ogg")
    else:
        print("❌ TTS не работает")


if __name__ == "__main__":
    asyncio.run(test_speechkit())