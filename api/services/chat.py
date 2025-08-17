import time
from typing import Optional
from ..schemas import ChatMessage, ChatResponse
from .. import main as api_main


async def simple_chat(message: ChatMessage, current_user: Optional[dict]) -> ChatResponse:
    response_text = await api_main.mas_integration.process_message(
        message.message,
        current_user["user_id"] if current_user else message.user_id,
    )
    return ChatResponse(response=response_text, agent="system", timestamp=time.time())


async def chat_with_visualization(message: ChatMessage, current_user: Optional[dict]) -> ChatResponse:
    # Delegate to existing handler for now
    return await api_main.send_message_with_visualization(message, current_user)