"""
Chat service for handling chat operations
"""
import time
import json
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from .base import BaseService
from ..schemas import ChatMessage, ChatResponse
from core.interfaces import IMessageProcessor
from memory.redis_store import RedisStore


class ChatService(BaseService):
    """Service for handling chat operations"""
    
    def __init__(self, message_processor: IMessageProcessor):
        super().__init__()
        self.message_processor = message_processor
        self.store = RedisStore(use_fallback=True)
        self.max_history_size = 100
    
    async def _setup(self) -> None:
        """Initialize chat service resources"""
        # Initialize message processor if needed
        if hasattr(self.message_processor, 'initialize'):
            await self.message_processor.initialize()
    
    async def _teardown(self) -> None:
        """Cleanup chat service resources"""
        if hasattr(self.message_processor, 'cleanup'):
            await self.message_processor.cleanup()
    
    async def process_simple_chat(self, message: ChatMessage, current_user: Optional[dict] = None) -> ChatResponse:
        """Process simple chat message"""
        user_id = current_user["user_id"] if current_user else message.user_id
        
        # Save message to history
        await self._save_to_history(user_id, "user", message.message)
        
        # Process through message processor
        response_text = await self.message_processor.process_message(
            message.message,
            user_id
        )
        
        # Save response to history
        await self._save_to_history(user_id, "assistant", response_text)
        
        return ChatResponse(
            response=response_text,
            agent="communicator",
            timestamp=time.time()
        )
    
    async def process_chat_with_visualization(self, message: ChatMessage, current_user: Optional[dict] = None) -> Dict[str, Any]:
        """Process chat with visualization data"""
        user_id = current_user["user_id"] if current_user else message.user_id
        
        # Generate flow ID for visualization
        flow_id = f"flow_{int(time.time() * 1000)}"
        
        # Save to history
        await self._save_to_history(user_id, "user", message.message)
        
        # Process message
        response_text = await self.message_processor.process_message(
            message.message,
            user_id
        )
        
        # Save response
        await self._save_to_history(user_id, "assistant", response_text)
        
        # Create visualization data
        visualization_data = {
            "flow_id": flow_id,
            "nodes": [
                {"id": "user", "label": "User", "type": "input"},
                {"id": "communicator", "label": "Communicator", "type": "agent"},
                {"id": "response", "label": "Response", "type": "output"}
            ],
            "edges": [
                {"from": "user", "to": "communicator"},
                {"from": "communicator", "to": "response"}
            ]
        }
        
        # Store visualization flow
        flow_key = f"visualization:flows:{flow_id}"
        # Используем asyncio.to_thread для синхронных операций Redis
        await asyncio.to_thread(
            self.store.set, 
            flow_key, 
            json.dumps(visualization_data), 
            3600
        )
        
        return {
            "response": response_text,
            "agent": "communicator",
            "timestamp": time.time(),
            "flow_id": flow_id,
            "visualization": visualization_data
        }
    
    async def get_chat_history(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get chat history for user"""
        history_key = f"chat_history:{user_id}"
        
        try:
            raw_history = await asyncio.to_thread(self.store.get, history_key)
            if raw_history:
                all_messages = json.loads(raw_history)
                messages = all_messages[offset:offset + limit]
                return {
                    "history": messages,
                    "total": len(all_messages),
                    "user_id": user_id,
                    "offset": offset,
                    "limit": limit
                }
        except Exception as e:
            self.logger.error(f"Error getting chat history: {e}")
        
        return {
            "history": [],
            "total": 0,
            "user_id": user_id,
            "offset": offset,
            "limit": limit
        }
    
    async def _save_to_history(self, user_id: str, role: str, content: str) -> None:
        """Save message to chat history"""
        history_key = f"chat_history:{user_id}"
        
        try:
            # Get existing history
            raw_history = await asyncio.to_thread(self.store.get, history_key)
            history = json.loads(raw_history) if raw_history else []
            
            # Add new message
            history.append({
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Trim history if too large
            if len(history) > self.max_history_size:
                history = history[-self.max_history_size:]
            
            # Save back
            await asyncio.to_thread(self.store.set, history_key, json.dumps(history))
            
        except Exception as e:
            self.logger.error(f"Error saving to history: {e}")


# Singleton instance
_chat_service: Optional[ChatService] = None


def get_chat_service(message_processor: IMessageProcessor) -> ChatService:
    """Get or create chat service instance"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService(message_processor)
    return _chat_service