"""
Потоковая обработка для real-time ответов в Root-MAS
"""
import asyncio
from typing import AsyncIterator, Dict, Any
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_agentchat.messages import TextMessage, StopMessage
from autogen_core import CancellationToken
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse
import json

class StreamingAgentManager:
    """Менеджер для потоковой обработки ответов агентов"""
    
    def __init__(self):
        self.agents = {}
        self.setup_agents()
    
    def setup_agents(self):
        """Инициализация агентов с поддержкой streaming"""
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        
        # Клиент с поддержкой streaming
        model_client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key="your-key",
            base_url="https://openrouter.ai/api/v1",
            # Важно: включаем streaming
            stream=True
        )
        
        self.agents["assistant"] = AssistantAgent(
            name="assistant",
            model_client=model_client,
            system_message="Ты помощник, который дает подробные ответы."
        )
    
    async def stream_response(
        self, 
        message: str, 
        user_id: str
    ) -> AsyncIterator[str]:
        """Генератор для потокового ответа"""
        # Создаем команду для streaming
        team = RoundRobinGroupChat(
            [self.agents["assistant"]], 
            max_turns=1
        )
        
        # Запускаем streaming
        stream = team.run_stream(task=message)
        
        # Обрабатываем поток
        async for message in stream:
            if hasattr(message, 'content'):
                # Отправляем частичный контент
                yield message.content
            
            # Можем добавить метаданные
            if hasattr(message, 'metadata'):
                yield f"\n[META]: {json.dumps(message.metadata)}\n"

# FastAPI приложение с streaming
app = FastAPI()
streaming_manager = StreamingAgentManager()

@app.get("/api/v1/chat/stream")
async def stream_chat(message: str, user_id: str):
    """Endpoint для потокового чата"""
    async def generate():
        """Генератор для SSE (Server-Sent Events)"""
        async for chunk in streaming_manager.stream_response(message, user_id):
            # Формат SSE
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Завершающее событие
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Отключаем буферизацию nginx
        }
    )

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint для streaming"""
    await websocket.accept()
    
    try:
        while True:
            # Получаем сообщение
            data = await websocket.receive_json()
            message = data.get("message", "")
            user_id = data.get("user_id", "")
            
            # Отправляем подтверждение
            await websocket.send_json({
                "type": "start",
                "message_id": data.get("message_id")
            })
            
            # Стримим ответ
            async for chunk in streaming_manager.stream_response(message, user_id):
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk,
                    "message_id": data.get("message_id")
                })
                
                # Небольшая задержка для визуального эффекта
                await asyncio.sleep(0.01)
            
            # Завершение
            await websocket.send_json({
                "type": "end",
                "message_id": data.get("message_id")
            })
            
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))

# Пример использования в Telegram боте
from telegram import Update
from telegram.ext import ContextTypes

async def stream_to_telegram(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    message: str
):
    """Потоковая отправка в Telegram"""
    chat_id = update.effective_chat.id
    
    # Отправляем начальное сообщение
    sent_message = await context.bot.send_message(
        chat_id=chat_id,
        text="💭 Думаю..."
    )
    
    # Буфер для накопления текста
    buffer = ""
    last_update_time = asyncio.get_event_loop().time()
    
    async for chunk in streaming_manager.stream_response(
        message, 
        str(chat_id)
    ):
        buffer += chunk
        
        # Обновляем сообщение каждые 0.5 секунды или при накоплении 100 символов
        current_time = asyncio.get_event_loop().time()
        if (current_time - last_update_time > 0.5 or 
            len(buffer) > 100):
            
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=sent_message.message_id,
                    text=buffer + "▌"  # Курсор печати
                )
                last_update_time = current_time
            except Exception:
                pass  # Игнорируем ошибки rate limit
    
    # Финальное обновление без курсора
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=sent_message.message_id,
        text=buffer
    )

# Пример с прерыванием streaming
class InterruptibleStreamingManager(StreamingAgentManager):
    """Менеджер с поддержкой прерывания"""
    
    def __init__(self):
        super().__init__()
        self.cancellation_tokens: Dict[str, CancellationToken] = {}
    
    async def stream_with_interruption(
        self, 
        message: str, 
        session_id: str
    ) -> AsyncIterator[str]:
        """Streaming с возможностью прерывания"""
        # Создаем токен отмены
        token = CancellationToken()
        self.cancellation_tokens[session_id] = token
        
        try:
            team = RoundRobinGroupChat(
                [self.agents["assistant"]], 
                max_turns=1
            )
            
            # Передаем токен в run_stream
            stream = team.run_stream(
                task=message,
                cancellation_token=token
            )
            
            async for chunk in stream:
                # Проверяем, не отменен ли запрос
                if token.is_cancelled():
                    yield "\n[ПРЕРВАНО ПОЛЬЗОВАТЕЛЕМ]"
                    break
                    
                yield chunk.content if hasattr(chunk, 'content') else str(chunk)
                
        finally:
            # Очищаем токен
            self.cancellation_tokens.pop(session_id, None)
    
    def interrupt_session(self, session_id: str):
        """Прерывание активной сессии"""
        if session_id in self.cancellation_tokens:
            self.cancellation_tokens[session_id].cancel()
            return True
        return False