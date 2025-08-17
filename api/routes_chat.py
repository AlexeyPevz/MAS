from fastapi import APIRouter, Depends, HTTPException
import time
from .schemas import ChatMessage, ChatResponse
from .security import rate_limit_dependency
from . import main as api_main

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse, dependencies=[Depends(rate_limit_dependency)])
async def message_with_visualization(message: ChatMessage, current_user: dict | None = None):
	return await api_main.send_message_with_visualization(message, current_user)