"""
Интеграция API с существующей MAS системой
"""

import logging
import os
from typing import Optional

# Используем фабрику для избежания циклических зависимостей
from core.factory import ComponentFactory
from core.interfaces import IMessageProcessor


logger = logging.getLogger(__name__)


class MASAPIIntegration:
    """Интеграция API с MAS системой"""
    
    def __init__(self):
        self.mas_system: Optional[object] = None
        self.mas_manager: Optional[IMessageProcessor] = None
        self._initialized = False
    
    async def initialize(self):
        """Инициализация MAS системы для API"""
        if self._initialized:
            return self.mas_manager
            
        try:
            logger.info("🔧 Инициализация MAS системы для API...")
            
            # Проверяем, использовать ли Teams API
            use_teams = os.getenv("USE_TEAMS_API", "true").lower() == "true"
            
            if use_teams:
                try:
                    # Пытаемся импортировать Teams manager динамически
                    import importlib.util
                    spec = importlib.util.find_spec("tools.teams_groupchat_manager")
                    if spec is not None:
                        teams_module = importlib.import_module("tools.teams_groupchat_manager")
                        if hasattr(teams_module, 'TEAMS_API_AVAILABLE') and teams_module.TEAMS_API_AVAILABLE:
                            logger.info("🏢 Используем Teams-enhanced GroupChat Manager")
                            self.mas_manager = teams_module.TeamsGroupChatManager()
                        else:
                            logger.warning("⚠️ Teams API недоступен, используем обычный менеджер")
                            self.mas_manager = ComponentFactory.create("mas_manager")
                    else:
                        logger.warning("⚠️ Teams manager не найден")
                        self.mas_manager = ComponentFactory.create("mas_manager")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось загрузить Teams manager: {e}")
                    self.mas_manager = ComponentFactory.create("mas_manager")
            else:
                # Создаем обычный менеджер через фабрику
                self.mas_manager = ComponentFactory.create("mas_manager")
                
            # Инициализируем если есть метод initialize
            if hasattr(self.mas_manager, 'initialize'):
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
            # Обрабатываем сообщение через интерфейс
            response = await self.mas_manager.process_message(message, user_id)
            return response or "Сообщение обработано агентами"
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения в MAS: {e}")
            return f"Ошибка обработки: {str(e)}"
    
    def get_agent_status(self):
        """Получение статуса агентов"""
        if not self._initialized or not self.mas_manager:
            return {}
        
        try:
            # Получаем статус агентов через интерфейс
            return self.mas_manager.get_agent_status()
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса агентов: {e}")
            return {}
    
    def get_system_metrics(self):
        """Получение системных метрик"""
        if not self._initialized or not self.mas_manager:
            return {}
        
        try:
            return self.mas_manager.get_system_metrics()
        except Exception as e:
            logger.error(f"❌ Ошибка получения метрик системы: {e}")
            return {}
    
    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            if hasattr(self.mas_manager, 'cleanup'):
                await self.mas_manager.cleanup()
            
            self._initialized = False
            logger.info("✅ MAS интеграция очищена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки MAS интеграции: {e}")


# Глобальный экземпляр интеграции
mas_integration = MASAPIIntegration()