"""
High-Performance Voice Processor
Оптимизированная обработка голосовых команд с использованием autogen-core
"""
import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib

# autogen-core imports
try:
    from autogen_core import (
        Agent,
        AgentRuntime,
        Message,
        MessageContext,
        TopicId,
        AgentId,
        default_subscription,
        message_handler
    )
    AUTOGEN_CORE_AVAILABLE = True
except ImportError:
    AUTOGEN_CORE_AVAILABLE = False
    Agent = object
    Message = object

# Yandex SpeechKit
try:
    from tools.yandex_speechkit import YandexSpeechKit
    SPEECHKIT_AVAILABLE = True
except ImportError:
    SPEECHKIT_AVAILABLE = False

logger = logging.getLogger(__name__)


# Определяем типы сообщений для голосовой обработки
@dataclass
class VoiceInputMessage(Message):
    """Входящее голосовое сообщение"""
    audio_data: bytes
    user_id: str
    chat_id: str
    format: str = "ogg"
    sample_rate: int = 48000
    language: str = "ru-RU"

@dataclass
class TextTranscriptionMessage(Message):
    """Результат транскрипции"""
    text: str
    confidence: float
    user_id: str
    chat_id: str
    processing_time: float

@dataclass
class VoiceOutputMessage(Message):
    """Сообщение для синтеза речи"""
    text: str
    user_id: str
    chat_id: str
    voice: str = "alena"
    emotion: str = "neutral"
    speed: float = 1.0

@dataclass
class AudioResponseMessage(Message):
    """Синтезированный аудио ответ"""
    audio_data: bytes
    user_id: str
    chat_id: str
    duration: float
    processing_time: float


# Высокопроизводительный агент распознавания речи
@default_subscription
class VoiceRecognitionAgent(Agent):
    """Агент для распознавания голоса с минимальной задержкой"""
    
    def __init__(self, speechkit_api_key: str):
        super().__init__()
        self.speechkit = YandexSpeechKit(speechkit_api_key) if SPEECHKIT_AVAILABLE else None
        self.cache = {}  # Локальный кэш для частых фраз
        self.stats = {
            "processed": 0,
            "cache_hits": 0,
            "avg_time": 0,
            "errors": 0
        }
        
    @message_handler
    async def handle_voice_input(self, message: VoiceInputMessage, ctx: MessageContext) -> None:
        """Обработка входящего голосового сообщения"""
        start_time = time.time()
        
        try:
            # Генерируем ключ для кэша
            audio_hash = hashlib.md5(message.audio_data[:1000]).hexdigest()
            
            # Проверяем кэш
            if audio_hash in self.cache:
                cached_text = self.cache[audio_hash]
                self.stats["cache_hits"] += 1
                processing_time = 0.001
                
                result = TextTranscriptionMessage(
                    text=cached_text,
                    confidence=1.0,
                    user_id=message.user_id,
                    chat_id=message.chat_id,
                    processing_time=processing_time
                )
            else:
                # Распознаем через SpeechKit
                if self.speechkit:
                    text = await self.speechkit.recognize_async(
                        message.audio_data,
                        lang=message.language
                    )
                    confidence = 0.95  # SpeechKit обычно дает высокую точность
                else:
                    # Fallback
                    text = "[Голосовое сообщение]"
                    confidence = 0.0
                
                processing_time = time.time() - start_time
                
                # Сохраняем в кэш короткие сообщения
                if len(message.audio_data) < 50000:  # ~3 секунды
                    self.cache[audio_hash] = text
                    # Ограничиваем размер кэша
                    if len(self.cache) > 1000:
                        # Удаляем старые записи
                        oldest_key = next(iter(self.cache))
                        del self.cache[oldest_key]
                
                result = TextTranscriptionMessage(
                    text=text,
                    confidence=confidence,
                    user_id=message.user_id,
                    chat_id=message.chat_id,
                    processing_time=processing_time
                )
            
            # Обновляем статистику
            self.stats["processed"] += 1
            self.stats["avg_time"] = (
                self.stats["avg_time"] * 0.9 + processing_time * 0.1
            )
            
            # Публикуем результат
            await ctx.publish(result, topic=TopicId("transcriptions"))
            
        except Exception as e:
            logger.error(f"Ошибка распознавания: {e}")
            self.stats["errors"] += 1
            
            # Отправляем сообщение об ошибке
            error_result = TextTranscriptionMessage(
                text="[Ошибка распознавания]",
                confidence=0.0,
                user_id=message.user_id,
                chat_id=message.chat_id,
                processing_time=time.time() - start_time
            )
            await ctx.publish(error_result, topic=TopicId("transcriptions"))


# Высокопроизводительный агент синтеза речи
@default_subscription
class VoiceSynthesisAgent(Agent):
    """Агент для синтеза речи с оптимизациями"""
    
    def __init__(self, speechkit_api_key: str):
        super().__init__()
        self.speechkit = YandexSpeechKit(speechkit_api_key) if SPEECHKIT_AVAILABLE else None
        self.synthesis_cache = {}  # Кэш синтезированной речи
        self.stats = {
            "synthesized": 0,
            "cache_hits": 0,
            "avg_time": 0,
            "total_duration": 0
        }
        
    @message_handler
    async def handle_voice_output(self, message: VoiceOutputMessage, ctx: MessageContext) -> None:
        """Синтез речи из текста"""
        start_time = time.time()
        
        try:
            # Ключ для кэша
            cache_key = f"{message.text}:{message.voice}:{message.emotion}:{message.speed}"
            cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Проверяем кэш
            if cache_hash in self.synthesis_cache:
                audio_data, duration = self.synthesis_cache[cache_hash]
                self.stats["cache_hits"] += 1
                processing_time = 0.001
            else:
                # Синтезируем через SpeechKit
                if self.speechkit:
                    audio_data = await self.speechkit.synthesize_async(
                        message.text,
                        voice=message.voice,
                        emotion=message.emotion,
                        speed=str(message.speed)
                    )
                    # Оценка длительности (примерная)
                    duration = len(message.text.split()) * 0.5
                else:
                    # Fallback
                    audio_data = b""
                    duration = 0.0
                
                processing_time = time.time() - start_time
                
                # Кэшируем короткие фразы
                if len(message.text) < 200:
                    self.synthesis_cache[cache_hash] = (audio_data, duration)
                    # Ограничиваем кэш
                    if len(self.synthesis_cache) > 500:
                        oldest_key = next(iter(self.synthesis_cache))
                        del self.synthesis_cache[oldest_key]
            
            # Обновляем статистику
            self.stats["synthesized"] += 1
            self.stats["avg_time"] = (
                self.stats["avg_time"] * 0.9 + processing_time * 0.1
            )
            self.stats["total_duration"] += duration
            
            # Публикуем результат
            result = AudioResponseMessage(
                audio_data=audio_data,
                user_id=message.user_id,
                chat_id=message.chat_id,
                duration=duration,
                processing_time=processing_time
            )
            
            await ctx.publish(result, topic=TopicId("audio_responses"))
            
        except Exception as e:
            logger.error(f"Ошибка синтеза: {e}")


# Координатор голосовой обработки
class VoiceProcessingCoordinator:
    """Координатор для управления голосовыми агентами"""
    
    def __init__(self, speechkit_api_key: str):
        self.runtime = AgentRuntime() if AUTOGEN_CORE_AVAILABLE else None
        self.recognition_agent = None
        self.synthesis_agent = None
        self.speechkit_api_key = speechkit_api_key
        self._initialized = False
        
    async def initialize(self):
        """Инициализация системы"""
        if not AUTOGEN_CORE_AVAILABLE:
            logger.warning("autogen-core недоступен")
            return
            
        if self._initialized:
            return
            
        # Создаем агентов
        self.recognition_agent = VoiceRecognitionAgent(self.speechkit_api_key)
        self.synthesis_agent = VoiceSynthesisAgent(self.speechkit_api_key)
        
        # Регистрируем в runtime
        self.runtime.register_agent(self.recognition_agent)
        self.runtime.register_agent(self.synthesis_agent)
        
        # Запускаем runtime в фоне
        self.runtime_task = asyncio.create_task(self.runtime.run())
        
        self._initialized = True
        logger.info("Voice Processing Coordinator initialized")
        
    async def process_voice_message(
        self,
        audio_data: bytes,
        user_id: str,
        chat_id: str,
        process_response: bool = True,
        response_callback: Optional[callable] = None
    ) -> Tuple[str, Optional[bytes]]:
        """Полный цикл обработки голосового сообщения"""
        
        if not self._initialized:
            await self.initialize()
            
        # Отправляем на распознавание
        voice_msg = VoiceInputMessage(
            audio_data=audio_data,
            user_id=user_id,
            chat_id=chat_id
        )
        
        # Создаем Future для результата
        transcription_future = asyncio.Future()
        audio_response_future = asyncio.Future()
        
        # Подписываемся на результаты (упрощенная версия)
        # В реальности нужен более сложный механизм подписки
        
        try:
            # Публикуем сообщение
            await self.runtime.publish(voice_msg, topic=TopicId("voice_inputs"))
            
            # Ждем результат (с таймаутом)
            # В реальной системе здесь был бы механизм подписки на результаты
            await asyncio.sleep(0.1)  # Даем время на обработку
            
            # Получаем результат распознавания
            result = await self._wait_for_task_result(task_id, timeout=30)
            if not result or result.get("status") != "completed":
                raise RuntimeError("Не удалось получить результат распознавания")
            
            transcribed_text = result.get("text", "")
            
            # Если нужен голосовой ответ
            audio_response = None
            if process_response and response_callback:
                # Получаем текстовый ответ
                text_response = await response_callback(transcribed_text)
                
                # Синтезируем речь
                voice_output = VoiceOutputMessage(
                    text=text_response,
                    user_id=user_id,
                    chat_id=chat_id
                )
                
                await self.runtime.publish(voice_output, topic=TopicId("voice_outputs"))
                await asyncio.sleep(0.1)  # Даем время на синтез
                
                # Mock audio response
                audio_response = b"synthesized_audio_data"
                
            return transcribed_text, audio_response
            
        except asyncio.TimeoutError:
            logger.error("Timeout processing voice message")
            return "[Timeout]", None
        except Exception as e:
            logger.error(f"Error processing voice: {e}")
            return f"[Error: {e}]", None
            
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики"""
        stats = {
            "core_available": AUTOGEN_CORE_AVAILABLE,
            "speechkit_available": SPEECHKIT_AVAILABLE,
            "initialized": self._initialized
        }
        
        if self.recognition_agent:
            stats["recognition"] = self.recognition_agent.stats
            
        if self.synthesis_agent:
            stats["synthesis"] = self.synthesis_agent.stats
            
        return stats
    
    async def _wait_for_task_result(self, task_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Ожидание результата задачи"""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            result = self.task_results.get(task_id)
            if result and result.get("status") in ["completed", "failed"]:
                return result
            await asyncio.sleep(0.1)
        
        return None
    
    async def shutdown(self):
        """Остановка системы"""
        if self.runtime_task:
            self.runtime_task.cancel()
            try:
                await self.runtime_task
            except asyncio.CancelledError:
                pass


# Пример использования
async def example_usage():
    """Пример использования оптимизированного голосового процессора"""
    
    api_key = os.getenv("YANDEX_API_KEY", "")
    if not api_key:
        print("❌ YANDEX_API_KEY не установлен")
        return
        
    # Создаем координатор
    coordinator = VoiceProcessingCoordinator(api_key)
    await coordinator.initialize()
    
    # Пример обработки
    # В реальном использовании audio_data должны быть получены из файла или потока
    # Например: audio_data = await read_audio_file("voice.ogg")
    
    # Callback для обработки текста
    async def process_text(text: str) -> str:
        return f"Вы сказали: {text}"
    
    # Пример: обработка реального аудио файла
    # with open("voice_message.ogg", "rb") as f:
    #     audio_data = f.read()
    #     user_id="test_user",
    #     chat_id="test_chat",
    #     process_response=True,
    #     response_callback=process_text
    # )
    
    # print(f"Распознанный текст: {text}")
    # print(f"Аудио ответ: {len(audio_response) if audio_response else 0} байт")
    
    # Статистика
    stats = coordinator.get_stats()
    print(f"\nСтатистика: {json.dumps(stats, indent=2)}")
    
    # Остановка
    await coordinator.shutdown()


if __name__ == "__main__":
    import os
    import json
    
    asyncio.run(example_usage())