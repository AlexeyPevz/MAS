"""
Core interfaces to break circular dependencies
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IMessageProcessor(ABC):
    """Interface for message processing"""
    
    @abstractmethod
    async def process_message(self, message: str, user_id: str = "default") -> str:
        """Process a message and return response"""
        pass
    
    @abstractmethod
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        pass
    
    @abstractmethod
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        pass


class IChatService(ABC):
    """Interface for chat service"""
    
    @abstractmethod
    async def chat_with_visualization(self, message: Dict[str, Any], user: Optional[Dict] = None) -> Dict[str, Any]:
        """Process chat with visualization"""
        pass


class IAPIClient(ABC):
    """Interface for API client"""
    
    @abstractmethod
    async def send_message(self, message: str, user_id: str = "default") -> Dict[str, Any]:
        """Send message to API"""
        pass