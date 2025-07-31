"""
Telegram Bot API Client
Клиент для подключения Telegram бота к Root-MAS API
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class TelegramAPIClient:
    """Клиент для работы с Root-MAS API из Telegram бота"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
    
    async def start(self):
        """Запуск клиента"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            logger.info(f"🔗 Telegram API клиент подключен к {self.api_base_url}")
    
    async def stop(self):
        """Остановка клиента"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("🔗 Telegram API клиент отключен")
    
    async def send_message(self, message: str, user_id: str = "telegram_user") -> str:
        """Отправка сообщения в MAS через API"""
        if not self.session:
            await self.start()
        
        try:
            payload = {
                "message": message,
                "user_id": user_id,
                "metadata": {
                    "source": "telegram",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            async with self.session.post(
                f"{self.api_base_url}/api/v1/chat/message",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "Ответ получен")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ API ошибка {response.status}: {error_text}")
                    return f"Ошибка сервера: {response.status}"
                    
        except asyncio.TimeoutError:
            logger.error("❌ Timeout при обращении к API")
            return "⏰ Время ожидания истекло, попробуйте позже"
            
        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка соединения с API: {e}")
            return "🔌 Проблема соединения с сервером"
            
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка API клиента: {e}")
            return f"❌ Ошибка: {str(e)}"
    
    async def get_chat_history(self, limit: int = 10) -> Dict[str, Any]:
        """Получение истории чата"""
        if not self.session:
            await self.start()
        
        try:
            async with self.session.get(
                f"{self.api_base_url}/api/v1/chat/history",
                params={"limit": limit},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"❌ Ошибка получения истории: {response.status}")
                    return {"messages": [], "total": 0}
                    
        except Exception as e:
            logger.error(f"❌ Ошибка получения истории: {e}")
            return {"messages": [], "total": 0}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        if not self.session:
            await self.start()
        
        try:
            async with self.session.get(
                f"{self.api_base_url}/api/v1/metrics/dashboard",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
                    
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_agents_status(self) -> Dict[str, Any]:
        """Получение статуса агентов"""
        if not self.session:
            await self.start()
        
        try:
            async with self.session.get(
                f"{self.api_base_url}/api/v1/agents/status",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    return {"agents": [], "total": 0}
                    
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса агентов: {e}")
            return {"agents": [], "total": 0}
    
    async def health_check(self) -> bool:
        """Проверка здоровья API"""
        if not self.session:
            await self.start()
        
        try:
            async with self.session.get(
                f"{self.api_base_url}/health",
                timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                return response.status == 200
                
        except Exception:
            return False


# Функция для создания callback для Telegram бота
def create_api_callback(api_base_url: str = "http://localhost:8000"):
    """Создает callback функцию для Telegram бота"""
    
    api_client = TelegramAPIClient(api_base_url)
    
    async def telegram_callback(message: str, user_id: str = "telegram_user") -> str:
        """Callback функция для обработки сообщений от Telegram"""
        try:
            # Проверяем здоровье API
            if not await api_client.health_check():
                return "🔧 Система временно недоступна, попробуйте позже"
            
            # Отправляем сообщение в API
            response = await api_client.send_message(message, user_id)
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка в telegram callback: {e}")
            return "❌ Произошла ошибка при обработке сообщения"
    
    return telegram_callback, api_client


# Тестовая функция
async def test_api_client():
    """Тест API клиента"""
    async with TelegramAPIClient() as client:
        print("🧪 Тестируем API клиент...")
        
        # Проверка здоровья
        health = await client.health_check()
        print(f"Health check: {health}")
        
        # Отправка сообщения
        response = await client.send_message("Привет, это тест!")
        print(f"Response: {response}")
        
        # Получение статуса
        status = await client.get_system_status()
        print(f"System status: {status}")


if __name__ == "__main__":
    asyncio.run(test_api_client())