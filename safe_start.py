#!/usr/bin/env python3
"""
Безопасный запуск API без лишних импортов
"""
import os
import sys

# Установим переменные окружения до импорта
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("REDIS_HOST", "localhost")

print("Starting safe API server...")

# Минимальный импорт FastAPI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Создаем простое приложение
app = FastAPI(title="Root-MAS Safe Mode")

class HealthResponse(BaseModel):
    status: str
    mode: str
    message: str

class ChatMessage(BaseModel):
    message: str
    user_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    agent: str = "system"

@app.get("/")
async def root():
    return {"status": "ok", "mode": "safe"}

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        mode="safe",
        message="API running in safe mode"
    )

@app.post("/api/v1/chat/simple", response_model=ChatResponse)
async def simple_chat(message: ChatMessage):
    """Простой эхо-чат для тестирования"""
    return ChatResponse(
        response=f"[Safe Mode] Received: {message.message}",
        agent="echo"
    )

# Попробуем импортировать основные компоненты
try:
    print("Trying to import MAS integration...")
    from api.integration import MASAPIIntegration
    mas_integration = MASAPIIntegration()
    
    @app.post("/api/v1/chat/mas", response_model=ChatResponse)
    async def mas_chat(message: ChatMessage):
        """Чат через MAS систему"""
        try:
            # Инициализируем MAS если нужно
            if not mas_integration._initialized:
                await mas_integration.initialize()
                
            response = await mas_integration.process_message(
                message.message, 
                message.user_id
            )
            return ChatResponse(response=response, agent="mas")
        except Exception as e:
            print(f"MAS Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    print("✅ MAS integration loaded")
    
except Exception as e:
    print(f"⚠️ Could not load MAS integration: {e}")
    print("Running in minimal mode")

if __name__ == "__main__":
    print("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")