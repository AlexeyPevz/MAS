"""
Fixed Root-MAS API Server
Исправленная версия без блокирующих операций и циклических импортов
"""
import os
import sys
import logging
import time
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone
from contextlib import asynccontextmanager

# Настройка логирования ДО импортов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Установка переменных окружения
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("REDIS_HOST", "localhost")

# FastAPI импорты
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# === Модели данных ===
class ChatMessage(BaseModel):
    message: str
    user_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    agent: str = "system"
    timestamp: float = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = time.time()
        super().__init__(**data)

class SystemMetrics(BaseModel):
    status: str
    uptime: str
    memory_usage: str = "N/A"
    cpu_usage: float = 0.0
    active_agents: int = 0
    cache_status: str = "N/A"

# === Глобальные переменные ===
class APIState:
    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.mas_manager = None
        self.redis_store = None
        self.initialized = False
        
api_state = APIState()

# === Lifecycle управление ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("🚀 Starting Root-MAS API...")
    try:
        await initialize_system()
        yield
    finally:
        # Shutdown
        logger.info("🛑 Shutting down Root-MAS API...")
        await cleanup_system()

# === Создание приложения ===
app = FastAPI(
    title="Root-MAS API (Fixed)",
    description="Multi-Agent System API - Fixed Version",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Инициализация системы ===
async def initialize_system():
    """Безопасная инициализация системы"""
    try:
        # 1. Redis с fallback
        logger.info("Initializing Redis store...")
        try:
            from memory.redis_store import RedisStore
            api_state.redis_store = RedisStore(use_fallback=True)
            logger.info("✅ Redis store initialized")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}, using in-memory only")
            from memory.in_memory_store import InMemoryStore
            api_state.redis_store = InMemoryStore()
        
        # 2. MAS Manager - отложенная инициализация
        logger.info("MAS Manager will be initialized on first use")
        
        api_state.initialized = True
        logger.info("✅ System initialization complete")
        
    except Exception as e:
        logger.error(f"❌ System initialization failed: {e}")
        # Продолжаем работу в деградированном режиме
        api_state.initialized = False

async def cleanup_system():
    """Очистка ресурсов"""
    pass

# === Lazy MAS Manager ===
async def get_mas_manager():
    """Ленивая инициализация MAS Manager"""
    if api_state.mas_manager is None:
        logger.info("Initializing MAS Manager...")
        try:
            from tools.smart_groupchat import SmartGroupChatManager
            api_state.mas_manager = SmartGroupChatManager()
            await api_state.mas_manager.initialize()
            logger.info("✅ MAS Manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MAS Manager: {e}")
            # Создаем заглушку
            api_state.mas_manager = MockMASManager()
    
    return api_state.mas_manager

# === Mock Manager для fallback ===
class MockMASManager:
    """Заглушка для MAS Manager"""
    async def process_message(self, message: str, user_id: str) -> str:
        return f"[Mock Response] Echo: {message}"
    
    def get_stats(self) -> dict:
        return {"status": "mock", "agents": 0}

# === API Endpoints ===

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "name": "Root-MAS API",
        "version": "2.0.0",
        "status": "running",
        "mode": "fixed"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    uptime = str(datetime.now(timezone.utc) - api_state.start_time)
    
    return {
        "status": "healthy" if api_state.initialized else "degraded",
        "uptime": uptime,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "api": "up",
            "mas": "ready" if api_state.mas_manager else "not_initialized",
            "redis": "up" if api_state.redis_store else "down"
        }
    }

@app.post("/api/v1/chat/simple", response_model=ChatResponse)
async def simple_chat(message: ChatMessage):
    """Простой chat endpoint"""
    try:
        # Получаем MAS Manager
        mas_manager = await get_mas_manager()
        
        # Обрабатываем сообщение
        response = await mas_manager.process_message(
            message.message,
            message.user_id
        )
        
        return ChatResponse(
            response=response,
            agent="mas" if api_state.mas_manager else "mock"
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        # Fallback на echo
        return ChatResponse(
            response=f"Echo: {message.message}",
            agent="echo"
        )

@app.get("/api/v1/system/metrics", response_model=SystemMetrics)
async def get_metrics():
    """Получение метрик системы"""
    uptime = str(datetime.now(timezone.utc) - api_state.start_time)
    
    # Безопасное получение метрик
    memory_usage = "N/A"
    cpu_usage = 0.0
    
    try:
        import psutil
        memory_usage = f"{psutil.virtual_memory().percent:.1f}%"
        cpu_usage = psutil.cpu_percent(interval=0.1)
    except:
        pass
    
    active_agents = 0
    if api_state.mas_manager and hasattr(api_state.mas_manager, 'agents'):
        active_agents = len(getattr(api_state.mas_manager, 'agents', {}))
    
    cache_status = "N/A"
    if api_state.redis_store:
        try:
            if hasattr(api_state.redis_store, '_is_using_fallback'):
                cache_status = "in-memory" if api_state.redis_store._is_using_fallback else "redis"
            else:
                cache_status = "active"
        except:
            pass
    
    return SystemMetrics(
        status="operational" if api_state.initialized else "degraded",
        uptime=uptime,
        memory_usage=memory_usage,
        cpu_usage=cpu_usage,
        active_agents=active_agents,
        cache_status=cache_status
    )

@app.post("/api/v1/chat/advanced", response_model=ChatResponse)
async def advanced_chat(message: ChatMessage):
    """Advanced chat с дополнительными функциями"""
    try:
        mas_manager = await get_mas_manager()
        
        # Проверяем семантический кэш
        cached_response = None
        if api_state.redis_store:
            cache_key = f"chat:{message.user_id}:{hash(message.message)}"
            cached_response = api_state.redis_store.get(cache_key)
        
        if cached_response:
            return ChatResponse(
                response=cached_response,
                agent="cache"
            )
        
        # Обрабатываем через MAS
        response = await mas_manager.process_message(
            message.message,
            message.user_id
        )
        
        # Сохраняем в кэш
        if api_state.redis_store and response:
            cache_key = f"chat:{message.user_id}:{hash(message.message)}"
            api_state.redis_store.set(cache_key, response, ttl=3600)
        
        return ChatResponse(
            response=response,
            agent="mas"
        )
        
    except Exception as e:
        logger.error(f"Advanced chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket для real-time чата"""
    await websocket.accept()
    
    try:
        mas_manager = await get_mas_manager()
        
        while True:
            # Получаем сообщение
            data = await websocket.receive_json()
            message = data.get("message", "")
            user_id = data.get("user_id", "ws_user")
            
            # Обрабатываем
            try:
                response = await mas_manager.process_message(message, user_id)
                
                # Отправляем ответ
                await websocket.send_json({
                    "response": response,
                    "agent": "mas",
                    "timestamp": time.time()
                })
                
            except Exception as e:
                await websocket.send_json({
                    "error": str(e),
                    "timestamp": time.time()
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

# === Дополнительные endpoints ===

@app.get("/api/v1/agents/list")
async def list_agents():
    """Список доступных агентов"""
    try:
        mas_manager = await get_mas_manager()
        if hasattr(mas_manager, 'agents'):
            return {
                "agents": list(mas_manager.agents.keys()),
                "count": len(mas_manager.agents)
            }
        return {"agents": [], "count": 0}
    except:
        return {"agents": [], "count": 0, "error": "MAS not initialized"}

@app.post("/api/v1/cache/clear")
async def clear_cache():
    """Очистка кэша"""
    if api_state.redis_store:
        try:
            if hasattr(api_state.redis_store, 'flushdb'):
                api_state.redis_store.flushdb()
            elif hasattr(api_state.redis_store, 'clear'):
                api_state.redis_store.clear()
            return {"status": "success", "message": "Cache cleared"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "Cache not available"}

# === Запуск ===
if __name__ == "__main__":
    import uvicorn
    
    # Запускаем сервер
    uvicorn.run(
        "fixed_main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Отключаем reload для стабильности
        log_level="info"
    )