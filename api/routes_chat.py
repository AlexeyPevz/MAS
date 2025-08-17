from fastapi import APIRouter, Depends
from .schemas import ChatMessage, ChatResponse
from .security import rate_limit_dependency
from .services import chat as chat_service

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse, dependencies=[Depends(rate_limit_dependency)])
async def message_with_visualization(message: ChatMessage, current_user: dict | None = None):
    return await chat_service.chat_with_visualization(message, current_user)