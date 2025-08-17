"""
Factory for creating components without circular dependencies
"""
from typing import Dict, Any, Optional, Callable
from .interfaces import IMessageProcessor, IChatService
import logging
import importlib

logger = logging.getLogger(__name__)


class ComponentFactory:
    """Factory for creating system components"""
    
    _registry: Dict[str, Callable] = {}
    _instances: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, name: str, creator: Callable):
        """Register a component creator"""
        cls._registry[name] = creator
    
    @classmethod
    def create(cls, name: str, *args, **kwargs) -> Any:
        """Create a component by name"""
        if name in cls._instances:
            return cls._instances[name]
        
        if name not in cls._registry:
            raise ValueError(f"Component '{name}' not registered")
        
        instance = cls._registry[name](*args, **kwargs)
        cls._instances[name] = instance
        return instance
    
    @classmethod
    def get_instance(cls, name: str) -> Optional[Any]:
        """Get existing instance"""
        return cls._instances.get(name)
    
    @classmethod
    def clear(cls):
        """Clear all instances"""
        cls._instances.clear()


def create_mas_manager(*args, **kwargs) -> IMessageProcessor:
    """Create MAS Manager without importing directly"""
    try:
        from tools.smart_groupchat import SmartGroupChatManager
        return SmartGroupChatManager(*args, **kwargs)
    except ImportError as e:
        logger.error(f"Failed to import SmartGroupChatManager: {e}")
        # Return a mock implementation
        class MockMASManager:
            async def process_message(self, message: str, user_id: str = "default") -> str:
                return f"Mock response to: {message}"
            
            def get_agent_status(self) -> Dict[str, Any]:
                return {"mock": {"active": True}}
            
            def get_system_metrics(self) -> Dict[str, Any]:
                return {"status": "mock"}
        
        return MockMASManager()


def create_telegram_bot(*args, **kwargs):
    """Create Telegram bot without importing directly"""
    try:
        from tools.modern_telegram_bot import ModernTelegramBot
        return ModernTelegramBot(*args, **kwargs)
    except ImportError as e:
        logger.error(f"Failed to import ModernTelegramBot: {e}")
        return None


def create_voice_processor(api_key: str):
    """Create voice processor without importing directly"""
    try:
        from tools.core_voice_processor import VoiceProcessingCoordinator
        return VoiceProcessingCoordinator(api_key)
    except ImportError as e:
        logger.error(f"Failed to import VoiceProcessingCoordinator: {e}")
        return None


# Register default creators
ComponentFactory.register("mas_manager", create_mas_manager)
ComponentFactory.register("telegram_bot", create_telegram_bot)
ComponentFactory.register("voice_processor", create_voice_processor)