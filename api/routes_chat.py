from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from .schemas import ChatMessage, ChatResponse
from .security import rate_limit_dependency
from .services.chat import get_chat_service
from .integration import mas_integration
import time
import logging

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
logger = logging.getLogger(__name__)

# Initialize chat service
chat_service = get_chat_service(mas_integration)


@router.post("/simple", response_model=ChatResponse, dependencies=[Depends(rate_limit_dependency)])
async def simple_chat(message: ChatMessage, current_user: dict | None = None):
    """Простой чат без визуализации"""
    try:
        # Initialize service if needed
        await chat_service.initialize()
        
        # Process through service
        return await chat_service.process_simple_chat(message, current_user)
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
        # Initialize service if needed
        await chat_service.initialize()
        
        # Get history through service
        return await chat_service.get_chat_history(user_id, limit, offset)
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения истории: {e}")
        raise HTTPException(status_code=500, detail=str(e))