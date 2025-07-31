"""
Yandex SpeechKit Client
Клиент для работы с Yandex SpeechKit (STT/TTS)
"""
import os
import logging
import base64
from typing import Optional, Dict, Any
import json

# Импорты с обработкой ошибок
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

logger = logging.getLogger(__name__)


class SpeechKitClient:
    """Клиент для работы с Yandex SpeechKit"""
    
    def __init__(self, api_key: str, folder_id: Optional[str] = None):
        """
        Инициализация клиента
        
        Args:
            api_key: API ключ Yandex Cloud
            folder_id: ID папки в Yandex Cloud
        """
        self.api_key = api_key
        self.folder_id = folder_id or os.getenv("YANDEX_FOLDER_ID", "")
        
        # Endpoints
        self.stt_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        self.tts_url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
        
        # Настройки по умолчанию
        self.default_voice = "alena"  # филипп, алена, эрмиль, джейн, мадирус, омаж, захар
        self.default_emotion = "neutral"  # neutral, good, evil
        self.default_speed = 1.0
        self.default_format = "oggopus"  # oggopus, mp3, wav
        
        logger.info("✅ SpeechKit клиент инициализирован")
    
    def speech_to_text(self, audio_data: bytes, format: str = "oggopus") -> Optional[str]:
        """
        Преобразование аудио в текст (STT)
        
        Args:
            audio_data: Аудио данные в байтах
            format: Формат аудио (oggopus, mp3, wav)
            
        Returns:
            Распознанный текст или None при ошибке
        """
        if not REQUESTS_AVAILABLE:
            logger.error("❌ requests не установлен. Установите: pip install requests")
            return None
        
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
        }
        
        params = {
            "format": format,
            "lang": "ru-RU",  # Язык распознавания
            "folderId": self.folder_id,
            "model": "general",  # general, numbers, dates, names, addresses
        }
        
        try:
            response = requests.post(
                self.stt_url,
                headers=headers,
                params=params,
                data=audio_data
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("result", "")
                logger.info(f"✅ STT успешно: {text[:50]}...")
                return text
            else:
                logger.error(f"❌ STT ошибка: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ STT исключение: {e}")
            return None
    
    def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        emotion: Optional[str] = None,
        speed: Optional[float] = None,
        format: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Преобразование текста в речь (TTS)
        
        Args:
            text: Текст для синтеза
            voice: Голос диктора
            emotion: Эмоциональная окраска
            speed: Скорость речи (0.1 - 3.0)
            format: Формат выходного аудио
            
        Returns:
            Аудио данные в байтах или None при ошибке
        """
        if not REQUESTS_AVAILABLE:
            logger.error("❌ requests не установлен. Установите: pip install requests")
            return None
        
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
        }
        
        data = {
            "text": text,
            "lang": "ru-RU",
            "voice": voice or self.default_voice,
            "emotion": emotion or self.default_emotion,
            "speed": speed or self.default_speed,
            "format": format or self.default_format,
            "folderId": self.folder_id,
        }
        
        try:
            response = requests.post(
                self.tts_url,
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                logger.info(f"✅ TTS успешно: {len(response.content)} байт")
                return response.content
            else:
                logger.error(f"❌ TTS ошибка: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ TTS исключение: {e}")
            return None
    
    async def async_speech_to_text(self, audio_data: bytes, format: str = "oggopus") -> Optional[str]:
        """
        Асинхронное преобразование аудио в текст (STT)
        """
        if not AIOHTTP_AVAILABLE:
            logger.error("❌ aiohttp не установлен. Установите: pip install aiohttp")
            return None
        
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
        }
        
        params = {
            "format": format,
            "lang": "ru-RU",
            "folderId": self.folder_id,
            "model": "general",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.stt_url,
                    headers=headers,
                    params=params,
                    data=audio_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        text = result.get("result", "")
                        logger.info(f"✅ Async STT успешно: {text[:50]}...")
                        return text
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Async STT ошибка: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Async STT исключение: {e}")
            return None
    
    async def async_text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        emotion: Optional[str] = None,
        speed: Optional[float] = None,
        format: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Асинхронное преобразование текста в речь (TTS)
        """
        if not AIOHTTP_AVAILABLE:
            logger.error("❌ aiohttp не установлен. Установите: pip install aiohttp")
            return None
        
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
        }
        
        data = {
            "text": text,
            "lang": "ru-RU",
            "voice": voice or self.default_voice,
            "emotion": emotion or self.default_emotion,
            "speed": speed or self.default_speed,
            "format": format or self.default_format,
            "folderId": self.folder_id,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.tts_url,
                    headers=headers,
                    data=data
                ) as response:
                    if response.status == 200:
                        content = await response.read()
                        logger.info(f"✅ Async TTS успешно: {len(content)} байт")
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Async TTS ошибка: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Async TTS исключение: {e}")
            return None
    
    def get_voices(self) -> Dict[str, Dict[str, Any]]:
        """
        Получение списка доступных голосов
        """
        return {
            "alena": {"lang": "ru-RU", "gender": "female", "emotion": ["neutral", "good"]},
            "filipp": {"lang": "ru-RU", "gender": "male", "emotion": ["neutral"]},
            "ermil": {"lang": "ru-RU", "gender": "male", "emotion": ["neutral", "good"]},
            "jane": {"lang": "ru-RU", "gender": "female", "emotion": ["neutral", "good", "evil"]},
            "madirus": {"lang": "ru-RU", "gender": "male", "emotion": ["neutral"]},
            "omazh": {"lang": "ru-RU", "gender": "female", "emotion": ["neutral", "evil"]},
            "zahar": {"lang": "ru-RU", "gender": "male", "emotion": ["neutral", "good"]},
        }
    
    def test_connection(self) -> bool:
        """
        Тестирование подключения к SpeechKit
        """
        try:
            # Пробуем синтезировать короткий текст
            audio = self.text_to_speech("Тест", format="mp3")
            return audio is not None
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования SpeechKit: {e}")
            return False


# Функция-заглушка для совместимости с коммуникатором
def run_telegram_bot(
    token: str,
    speechkit_client: SpeechKitClient,
    forward_callback: Any
) -> None:
    """
    Заглушка для запуска Telegram бота с SpeechKit
    В реальной реализации здесь должна быть интеграция с modern_telegram_bot
    """
    logger.warning("⚠️ run_telegram_bot - заглушка. Используйте ModernTelegramBot напрямую")
    
    # Импортируем и запускаем современный бот
    try:
        from .modern_telegram_bot import ModernTelegramBot
        import asyncio
        
        # Создаем обертку для интеграции SpeechKit
        async def enhanced_callback(message: str) -> str:
            # Вызываем оригинальный callback
            result = forward_callback(message)
            
            # Опционально: синтезируем ответ в речь
            # audio = speechkit_client.text_to_speech(result)
            
            return result
        
        # Создаем и запускаем бота
        bot = ModernTelegramBot(token, enhanced_callback, enable_voice=True)
        
        # Добавляем SpeechKit в бота для обработки голосовых сообщений
        bot.speechkit = speechkit_client
        
        # Запускаем
        asyncio.run(bot.run())
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска Telegram бота: {e}")
        raise


if __name__ == "__main__":
    # Тестирование клиента
    api_key = os.getenv("YANDEX_API_KEY")
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    
    if not api_key:
        print("❌ YANDEX_API_KEY не установлен")
    else:
        client = SpeechKitClient(api_key, folder_id)
        
        # Тест TTS
        print("🎤 Тестирование TTS...")
        audio = client.text_to_speech("Привет, это тест синтеза речи!")
        if audio:
            print(f"✅ TTS работает, получено {len(audio)} байт")
            
            # Сохраняем в файл
            with open("test_tts.ogg", "wb") as f:
                f.write(audio)
            print("💾 Аудио сохранено в test_tts.ogg")
        else:
            print("❌ TTS не работает")
        
        # Показываем доступные голоса
        print("\n🎭 Доступные голоса:")
        for voice, info in client.get_voices().items():
            print(f"  • {voice}: {info}")