"""
Root-MAS API Server
Единый API для всех клиентов: PWA, Telegram Bot, Mini App
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Импорты MAS системы
from tools.smart_groupchat import SmartGroupChatManager
from tools.modern_telegram_bot import ModernTelegramBot
from config.config_loader import load_config
from api.integration import mas_integration


# Pydantic модели для API
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "api_user"
    metadata: Optional[Dict[str, Any]] = {}


class ChatResponse(BaseModel):
    response: str
    timestamp: datetime
    agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class AgentStatus(BaseModel):
    name: str
    status: str
    last_activity: Optional[datetime] = None
    message_count: int = 0


class SystemMetrics(BaseModel):
    total_messages: int
    active_agents: int
    uptime: str
    memory_usage: Optional[str] = None
    cpu_usage: Optional[float] = None


class ProjectInfo(BaseModel):
    id: str
    name: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime


# Global state
class APIState:
    def __init__(self):
        self.mas_manager: Optional[SmartGroupChatManager] = None
        self.telegram_bot: Optional[ModernTelegramBot] = None
        self.websocket_connections: List[WebSocket] = []
        self.start_time = datetime.now()
        self.message_history: List[Dict[str, Any]] = []


# Глобальное состояние API
api_state = APIState()
logger = logging.getLogger(__name__)


# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом API"""
    logger.info("🚀 Запуск Root-MAS API...")
    
    # Startup
    await initialize_mas_system()
    
    yield
    
    # Shutdown
    logger.info("🛑 Остановка Root-MAS API...")
    await cleanup_resources()


# FastAPI app
app = FastAPI(
    title="Root-MAS API",
    description="Единый API для многоагентной системы",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def initialize_mas_system():
    """Инициализация MAS системы"""
    try:
        logger.info("🔧 Инициализация MAS системы...")
        
        # Инициализируем MAS через интеграционный модуль
        api_state.mas_manager = await mas_integration.initialize()
        
        logger.info("✅ MAS система инициализирована")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации MAS: {e}")
        raise


async def cleanup_resources():
    """Очистка ресурсов"""
    try:
        # Закрытие WebSocket соединений
        for ws in api_state.websocket_connections:
            try:
                await ws.close()
            except:
                pass
        
        # Остановка Telegram бота
        if api_state.telegram_bot:
            await api_state.telegram_bot.shutdown()
        
        # Очистка MAS интеграции
        await mas_integration.cleanup()
            
        logger.info("✅ Ресурсы очищены")
        
    except Exception as e:
        logger.error(f"❌ Ошибка очистки ресурсов: {e}")


def get_mas_manager():
    """Dependency для получения MAS менеджера"""
    if not api_state.mas_manager:
        raise HTTPException(status_code=503, detail="MAS система не инициализирована")
    return api_state.mas_manager


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Root-MAS API",
        "version": "1.0.0",
        "status": "running",
        "uptime": str(datetime.now() - api_state.start_time)
    }


@app.get("/health")
async def health_check():
    """Health check для мониторинга"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "components": {
            "mas_system": api_state.mas_manager is not None,
            "telegram_bot": api_state.telegram_bot is not None,
            "websockets": len(api_state.websocket_connections)
        }
    }


# =============================================================================
# CHAT API - для диалога с Communicator Agent
# =============================================================================

@app.post("/api/v1/chat/message", response_model=ChatResponse)
async def send_message(
    chat_msg: ChatMessage,
    mas_manager = Depends(get_mas_manager)
):
    """Отправка сообщения в MAS через Communicator Agent"""
    try:
        logger.info(f"📨 Получено сообщение: {chat_msg.message[:100]}...")
        
        # Обработка через MAS
        if mas_manager:
            response = await mas_manager.process_user_message(chat_msg.message)
        else:
            # Заглушка пока MAS не инициализирован
            response = f"Echo: {chat_msg.message}"
        
        # Создаем ответ
        chat_response = ChatResponse(
            response=response,
            timestamp=datetime.now(),
            agent="communicator",
            metadata={"user_id": chat_msg.user_id}
        )
        
        # Сохраняем в историю
        api_state.message_history.append({
            "timestamp": chat_response.timestamp,
            "user_message": chat_msg.message,
            "agent_response": response,
            "user_id": chat_msg.user_id
        })
        
        # Уведомляем WebSocket клиентов
        await broadcast_to_websockets({
            "type": "new_message",
            "data": chat_response.dict()
        })
        
        return chat_response
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/chat/history")
async def get_chat_history(limit: int = 50, offset: int = 0):
    """Получение истории чата"""
    try:
        total = len(api_state.message_history)
        history = api_state.message_history[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "messages": history
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения истории: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# METRICS API - для метрик и мониторинга
# =============================================================================

@app.get("/api/v1/metrics/dashboard", response_model=SystemMetrics)
async def get_dashboard_metrics():
    """Метрики для дашборда"""
    try:
        import psutil
        
        uptime = str(datetime.now() - api_state.start_time)
        memory = f"{psutil.virtual_memory().percent:.1f}%"
        cpu = psutil.cpu_percent(interval=1)
        
        return SystemMetrics(
            total_messages=len(api_state.message_history),
            active_agents=12 if api_state.mas_manager else 0,  # Placeholder
            uptime=uptime,
            memory_usage=memory,
            cpu_usage=cpu
        )
        
    except ImportError:
        # Fallback если psutil не установлен
        return SystemMetrics(
            total_messages=len(api_state.message_history),
            active_agents=12 if api_state.mas_manager else 0,
            uptime=str(datetime.now() - api_state.start_time)
        )
    except Exception as e:
        logger.error(f"❌ Ошибка получения метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/agents/status")
async def get_agents_status():
    """Статус всех агентов"""
    try:
        # Пока заглушка, потом интегрируем с реальными агентами
        agents = [
            AgentStatus(name="meta", status="active", message_count=15),
            AgentStatus(name="communicator", status="active", message_count=32),
            AgentStatus(name="researcher", status="idle", message_count=8),
            AgentStatus(name="coordination", status="active", message_count=12),
        ]
        
        return {"agents": agents, "total": len(agents)}
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса агентов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PROJECTS API - для управления проектами
# =============================================================================

@app.get("/api/v1/projects")
async def get_projects():
    """Список проектов"""
    try:
        # Заглушка, потом интегрируем с базой данных
        projects = [
            ProjectInfo(
                id="proj_1",
                name="Root-MAS Development",
                description="Разработка многоагентной системы",
                status="active",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        return {"projects": projects, "total": len(projects)}
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения проектов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# LOGS API - для просмотра логов
# =============================================================================

@app.get("/api/v1/logs")
async def get_logs(level: str = "INFO", limit: int = 100):
    """Получение системных логов"""
    try:
        # Пока заглушка, потом интегрируем с файлами логов
        logs = [
            {
                "timestamp": datetime.now(),
                "level": "INFO",
                "message": "Система запущена успешно",
                "component": "api"
            }
        ]
        
        return {"logs": logs, "total": len(logs)}
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения логов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WEBSOCKET для real-time обновлений
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time коммуникации"""
    await websocket.accept()
    api_state.websocket_connections.append(websocket)
    
    try:
        while True:
            # Ожидаем сообщения от клиента
            data = await websocket.receive_text()
            logger.info(f"🔌 WebSocket сообщение: {data}")
            
            # Можно обрабатывать команды от клиента
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket отключен")
    finally:
        if websocket in api_state.websocket_connections:
            api_state.websocket_connections.remove(websocket)


async def broadcast_to_websockets(message: Dict[str, Any]):
    """Отправка сообщения всем WebSocket клиентам"""
    if not api_state.websocket_connections:
        return
        
    import json
    message_text = json.dumps(message, default=str)
    
    # Удаляем отключенные соединения
    disconnected = []
    
    for ws in api_state.websocket_connections:
        try:
            await ws.send_text(message_text)
        except:
            disconnected.append(ws)
    
    # Очищаем отключенные соединения
    for ws in disconnected:
        api_state.websocket_connections.remove(ws)


# =============================================================================
# AUTOGEN STUDIO PROXY - для интеграции с существующим Studio
# =============================================================================

@app.get("/api/v1/studio/logs")
async def get_studio_logs():
    """Прокси для AutoGen Studio логов"""
    try:
        # Здесь можно проксировать запросы к AutoGen Studio
        # или читать логи напрямую из файлов
        return {"message": "Studio logs integration - TODO"}
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения Studio логов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Запуск сервера
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )