"""
Интеграция API с существующей MAS системой
"""

import logging
from typing import Optional

# Интеграция будет через существующие компоненты
from tools.smart_groupchat import SmartGroupChatManager


logger = logging.getLogger(__name__)


class MASAPIIntegration:
    """Интеграция API с MAS системой"""
    
    def __init__(self):
        self.mas_system: Optional[object] = None
        self.mas_manager: Optional[SmartGroupChatManager] = None
        self._initialized = False
    
    async def initialize(self):
        """Инициализация MAS системы для API"""
        if self._initialized:
            return self.mas_manager
            
        try:
            logger.info("🔧 Инициализация MAS системы для API...")
            
            # Создаем менеджер напрямую для API использования
            from tools.smart_groupchat import SmartGroupChatManager
            self.mas_manager = SmartGroupChatManager()
            await self.mas_manager.initialize()
            
            self._initialized = True
            logger.info("✅ MAS система инициализирована для API")
            
            return self.mas_manager
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации MAS для API: {e}")
            raise
    
    async def process_message(self, message: str, user_id: str = "api_user") -> str:
        """Обработка сообщения через MAS"""
        if not self._initialized or not self.mas_manager:
            await self.initialize()
        
        try:
            # Обрабатываем сообщение через Communicator Agent
            response = await self.mas_manager.process_user_message(message)
            return response or "Сообщение обработано агентами"
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения в MAS: {e}")
            return f"Ошибка обработки: {str(e)}"
    
    def get_agent_status(self):
        """Получение статуса агентов"""
        if not self._initialized or not self.mas_manager:
            return []
        
        try:
            # Получаем статус агентов из менеджера
            return self.mas_manager.get_agent_statistics()
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса агентов: {e}")
            return {}
    
    def get_system_metrics(self):
        """Получение системных метрик"""
        if not self._initialized or not self.mas_manager:
            return {}
        
        try:
            return self.mas_manager.get_system_status()
        except Exception as e:
            logger.error(f"❌ Ошибка получения метрик системы: {e}")
            return {}
    
    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            if self.mas_system:
                await self.mas_system._cleanup()
            
            self._initialized = False
            logger.info("✅ MAS интеграция очищена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки MAS интеграции: {e}")


# Глобальный экземпляр интеграции
mas_integration = MASAPIIntegration()