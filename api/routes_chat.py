from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from .schemas import ChatMessage, ChatResponse
from .security import rate_limit_dependency
from .services import chat as chat_service
from .integration import mas_integration
import time
import logging

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/simple", response_model=ChatResponse, dependencies=[Depends(rate_limit_dependency)])
async def simple_chat(message: ChatMessage, current_user: dict | None = None):
    """Простой чат без визуализации"""
    try:
        # Process through MAS
        response_text = await mas_integration.process_message(message.message, message.user_id)
        
        return ChatResponse(
            response=response_text,
            agent="communicator",
            timestamp=time.time()
        )
    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=ChatResponse, dependencies=[Depends(rate_limit_dependency)])
async def chat(message: ChatMessage, current_user: dict | None = None):
    """Основной эндпоинт чата - алиас для simple"""
    return await simple_chat(message, current_user)


@router.post("/message", response_model=ChatResponse, dependencies=[Depends(rate_limit_dependency)])
async def message_with_visualization(message: ChatMessage, current_user: dict | None = None):
    return await chat_service.chat_with_visualization(message, current_user)


@router.get("/history")
async def get_chat_history(user_id: str = "default", limit: int = 50, offset: int = 0):
    """Получение истории чата"""
    try:
        # Get history from Redis or in-memory storage
        from memory.redis_store import RedisStore
        store = RedisStore(use_fallback=True)
        
        # Get all messages for user
        history_key = f"chat_history:{user_id}"
        messages = []
        
        # Try to get from Redis
        try:
            raw_history = store.get(history_key)
            if raw_history:
                import json
                all_messages = json.loads(raw_history)
                messages = all_messages[offset:offset + limit]
                return {
                    "history": messages,
                    "total": len(all_messages),
                    "user_id": user_id,
                    "offset": offset,
                    "limit": limit
                }
        except Exception:
            pass
        
        # Return empty if no history
        return {
            "history": [],
            "total": 0,
            "user_id": user_id,
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения истории: {e}")
        raise HTTPException(status_code=500, detail=str(e))