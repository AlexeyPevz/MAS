"""
Root-MAS API Server
Единый API для всех клиентов: PWA, Telegram Bot, Mini App
"""

import os
import asyncio
import logging
import time
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from pathlib import Path

import httpx

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks, Header, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi.security import HTTPAuthorizationCredentials
from .settings import settings

# Импорты MAS системы через фабрику для избежания циклических зависимостей
from core.factory import ComponentFactory
from config.config_loader import load_config
from api.integration import mas_integration
from tools import studio_logger
from api.security import rate_limit_dependency, require_permission, Role, auth_user_dependency, check_permission
from api.security import Token as AuthTokenModel
from api.security import security_manager, SECRET_KEY, ALGORITHM
import jwt
from tools.multitool import (
    list_tools, list_workflows, list_apps,
    get_tool_versions, get_workflow_versions, get_app_versions,
    rollback_tool, rollback_workflow, rollback_app,
)

# Import federation
try:
    from tools.federated_learning import federation_hub
    FEDERATION_ENABLED = True
except ImportError:
    FEDERATION_ENABLED = False

# Import semantic cache
try:
    from tools.semantic_llm_cache import semantic_cache
    SEMANTIC_CACHE_ENABLED = True
except ImportError:
    SEMANTIC_CACHE_ENABLED = False


# Pydantic модели для API
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="Message text")
    user_id: Optional[str] = Field(default="api_user", regex=r'^[a-zA-Z0-9_-]+$', max_length=100)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    response: str
    timestamp: float
    agent: Optional[str] = None
    flow_id: Optional[str] = None
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


# Новые модели для визуализации мыслительного процесса
class AgentThought(BaseModel):
    agent_id: str
    agent_name: str
    message: str
    thought_type: str  # "receiving", "thinking", "responding", "forwarding"
    timestamp: float
    duration_ms: Optional[int] = None
    target_agent: Optional[str] = None

class AgentProfile(BaseModel):
    agent_id: str
    name: str
    role: str
    avatar_url: str
    description: str
    capabilities: List[str]

# Загружаем конфигурацию системы и формируем профили агентов
CONFIG = load_config()
AGENTS_CONFIG = CONFIG.get("agents", {})
AGENT_PROFILES = [
    AgentProfile(
        agent_id=name,
        name=cfg.get("role", name),
        role=cfg.get("role", ""),
        avatar_url=cfg.get("avatar_url", ""),
        description=cfg.get("description", ""),
        capabilities=cfg.get("capabilities", []),
    )
    for name, cfg in AGENTS_CONFIG.items()
]

class MessageFlow(BaseModel):
    flow_id: str
    user_message: str
    current_agent: str
    flow_stage: str  # "user_to_communicator", "communicator_thinking", "group_chat", "agent_processing", "response_generation"
    thoughts: List[AgentThought]
    timestamp: float

class ThoughtVisualizationEvent(BaseModel):
    event_type: str  # "thought_start", "thought_update", "thought_complete", "message_flow"
    flow_id: str
    data: Dict[str, Any]

# =============================
# Auth models moved to routes_auth.py

# Менеджер WebSocket подключений для визуализации
class VisualizationWebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.message_flows: Dict[str, MessageFlow] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast_thought_event(self, event: ThoughtVisualizationEvent):
        """Отправка события мыслительного процесса всем подключенным клиентам"""
        if self.active_connections:
            event_data = event.dict()
            logger.info(f"🧠 Broadcasting thought event: {event.event_type} for flow {event.flow_id}")
            
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(json.dumps(event_data))
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки WebSocket: {e}")
                    disconnected.append(connection)
            
            # Удаляем отключенные соединения
            for conn in disconnected:
                self.disconnect(conn)
    
    async def start_message_flow(self, user_message: str, user_id: str) -> str:
        """Начало нового потока обработки сообщения"""
        flow_id = f"flow_{int(time.time() * 1000)}_{user_id}"
        
        message_flow = MessageFlow(
            flow_id=flow_id,
            user_message=user_message,
            current_agent="communicator",
            flow_stage="user_to_communicator",
            thoughts=[],
            timestamp=time.time()
        )
        
        self.message_flows[flow_id] = message_flow
        
        # Отправляем событие начала потока
        await self.broadcast_thought_event(ThoughtVisualizationEvent(
            event_type="message_flow_start",
            flow_id=flow_id,
            data={
                "user_message": user_message,
                "user_id": user_id,
                "timestamp": time.time()
            }
        ))
        
        return flow_id
    
    async def add_agent_thought(self, flow_id: str, thought: AgentThought):
        """Добавление мысли агента в поток"""
        if flow_id in self.message_flows:
            self.message_flows[flow_id].thoughts.append(thought)
            self.message_flows[flow_id].current_agent = thought.agent_id
            
            # Отправляем событие новой мысли
            await self.broadcast_thought_event(ThoughtVisualizationEvent(
                event_type="agent_thought",
                flow_id=flow_id,
                data=thought.dict()
            ))
    
    async def update_flow_stage(self, flow_id: str, new_stage: str, current_agent: str = None):
        """Обновление стадии обработки потока"""
        if flow_id in self.message_flows:
            self.message_flows[flow_id].flow_stage = new_stage
            if current_agent:
                self.message_flows[flow_id].current_agent = current_agent
            
            await self.broadcast_thought_event(ThoughtVisualizationEvent(
                event_type="flow_stage_update",
                flow_id=flow_id,
                data={
                    "new_stage": new_stage,
                    "current_agent": current_agent
                }
            ))
    
    async def complete_message_flow(self, flow_id: str, final_response: str):
        """Завершение потока обработки сообщения"""
        if flow_id in self.message_flows:
            await self.broadcast_thought_event(ThoughtVisualizationEvent(
                event_type="message_flow_complete",
                flow_id=flow_id,
                data={
                    "final_response": final_response,
                    "total_thoughts": len(self.message_flows[flow_id].thoughts),
                    "duration_ms": int((time.time() - self.message_flows[flow_id].timestamp) * 1000)
                }
            ))
            
            # Очищаем старые потоки (оставляем только последние 10)
            if len(self.message_flows) > 10:
                oldest_flow = min(self.message_flows.keys(), 
                                key=lambda k: self.message_flows[k].timestamp)
                del self.message_flows[oldest_flow]

# Глобальный менеджер визуализации
visualization_manager = VisualizationWebSocketManager()


# Global state
class APIState:
    def __init__(self):
        self.groupchat_manager: Optional[SmartGroupChatManager] = None
        self.telegram_bot: Optional[ModernTelegramBot] = None
        self.websocket_connections: List[WebSocket] = []
        self.start_time = datetime.now(timezone.utc)
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

# Mount routers (progressive extraction)
from .routes_chat import router as chat_router
from .routes_voice import router as voice_router
from .routes_metrics import router as metrics_router
from .routes_registry import router as registry_router
from .routes_auth import router as auth_router
from .routes_cache import router as cache_router
from .routes_federation import router as federation_router
from .routes_misc import router as misc_router
from .routes_agents import router as agents_router
from .routes_websocket import router as websocket_router
from .routes_studio import router as studio_router

app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(metrics_router)
app.include_router(registry_router)
app.include_router(auth_router)
app.include_router(cache_router)
app.include_router(federation_router)
app.include_router(misc_router)
app.include_router(agents_router)
app.include_router(websocket_router)
app.include_router(studio_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Secret"],
)

# Security middlewares from settings
if settings.trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
if settings.enforce_https:
    app.add_middleware(HTTPSRedirectMiddleware)

# Путь к PWA статике
pwa_path = Path(__file__).resolve().parent.parent / "pwa"
if pwa_path.exists():
    app.mount("/pwa", StaticFiles(directory=str(pwa_path), html=True), name="pwa")
    from fastapi.responses import RedirectResponse
    @app.get("/app", include_in_schema=False)
    async def redirect_to_pwa():
        return RedirectResponse(url="/pwa/")


async def initialize_mas_system():
    """Инициализация MAS системы"""
    try:
        logger.info("🔧 Инициализация MAS системы...")
        
        # Инициализируем MAS через интеграционный модуль
        api_state.groupchat_manager = await mas_integration.initialize()
        
        # Инициализируем семантический кэш если доступен
        if SEMANTIC_CACHE_ENABLED:
            logger.info("🧠 Инициализация семантического кэша...")
            await semantic_cache.initialize()
            logger.info("✅ Семантический кэш инициализирован")
        
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
    if not api_state.groupchat_manager:
        raise HTTPException(status_code=503, detail="MAS система не инициализирована")
    return api_state.groupchat_manager


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    return {
        "message": "Root-MAS API", 
        "version": "0.4.0",
        "docs": "/docs",
        "pwa": "/pwa"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint для мониторинга"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "api": "up",
            "agents": "up"
        }
    }
    
    # Check Redis
    try:
        from memory.redis_store import RedisStore
        redis = RedisStore()
        redis.set("health_check", "ok", ttl=10)
        health_status["services"]["redis"] = "up"
    except Exception:
        health_status["services"]["redis"] = "down"
        health_status["status"] = "degraded"
    
    # Check agents
    try:
        if api_state.groupchat_manager and api_state.groupchat_manager.agents:
            health_status["services"]["agents_count"] = len(api_state.groupchat_manager.agents)
        else:
            health_status["services"]["agents"] = "initializing"
    except Exception:
        health_status["services"]["agents"] = "error"
        health_status["status"] = "unhealthy"
    
    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


# =============================================================================
# VOICE API - для голосовых функций
# =============================================================================

# Voice endpoints moved to routes_voice.py

# =============================================================================
# CHAT API - для диалога с Communicator Agent
# =============================================================================

# Chat endpoints moved to routes_chat.py


# Chat/message endpoint moved to routes_chat.py

# Функция симуляции мыслительного процесса (временная)
async def simulate_agent_thinking(flow_id: str, user_message: str):
    """Симуляция мыслительного процесса агентов для демонстрации"""
    
    # 1. Сообщение попадает к коммуникатору
    await visualization_manager.add_agent_thought(flow_id, AgentThought(
        agent_id="communicator",
        agent_name="Коммуникатор", 
        message=f"Получено сообщение: '{user_message}'",
        thought_type="receiving",
        timestamp=time.time()
    ))
    
    await asyncio.sleep(0.5)
    
    # 2. Коммуникатор думает
    await visualization_manager.add_agent_thought(flow_id, AgentThought(
        agent_id="communicator",
        agent_name="Коммуникатор",
        message="Анализирую сообщение и определяю, нужно ли обращаться к группе агентов...",
        thought_type="thinking", 
        timestamp=time.time()
    ))
    
    await asyncio.sleep(1.0)
    
    # 3. Коммуникатор передает в групп-чат
    await visualization_manager.update_flow_stage(flow_id, "group_chat", "meta_agent")
    await visualization_manager.add_agent_thought(flow_id, AgentThought(
        agent_id="communicator", 
        agent_name="Коммуникатор",
        message="Передаю сообщение мета-агенту для распределения задач",
        thought_type="forwarding",
        timestamp=time.time(),
        target_agent="meta_agent"
    ))
    
    await asyncio.sleep(0.5)
    
    # 4. Мета-агент получает и анализирует
    await visualization_manager.add_agent_thought(flow_id, AgentThought(
        agent_id="meta_agent",
        agent_name="Мета-Агент",
        message="Получил задачу от коммуникатора. Анализирую сложность...",
        thought_type="receiving", 
        timestamp=time.time()
    ))
    
    await asyncio.sleep(1.0)
    
    await visualization_manager.add_agent_thought(flow_id, AgentThought(
        agent_id="meta_agent",
        agent_name="Мета-Агент", 
        message="Определяю, какие агенты должны участвовать в решении задачи",
        thought_type="thinking",
        timestamp=time.time()
    ))
    
    await asyncio.sleep(1.5)
    
    # 5. Мета-агент распределяет задачи
    await visualization_manager.update_flow_stage(flow_id, "agent_processing")
    
    # Используем агентов, которые точно есть в конфигурации
    selected_agents = ["researcher", "multitool", "communicator"]
    for agent_id in selected_agents:
        agent_name = next((p.name for p in AGENT_PROFILES if p.agent_id == agent_id), agent_id.title())
        
        await visualization_manager.add_agent_thought(flow_id, AgentThought(
            agent_id="meta_agent",
            agent_name="Мета-Агент",
            message=f"Направляю задачу агенту '{agent_name}'",
            thought_type="forwarding",
            timestamp=time.time(),
            target_agent=agent_id
        ))
        
        await asyncio.sleep(0.3)
        
        # Агент получает и обрабатывает
        await visualization_manager.add_agent_thought(flow_id, AgentThought(
            agent_id=agent_id,
            agent_name=agent_name,
            message=f"Получил задачу от мета-агента. Начинаю обработку...",
            thought_type="receiving",
            timestamp=time.time()
        ))
        
        await asyncio.sleep(0.8)
        
        await visualization_manager.add_agent_thought(flow_id, AgentThought(
            agent_id=agent_id,
            agent_name=agent_name,
            message=f"Выполняю анализ с использованием моих навыков...",
            thought_type="thinking",
            timestamp=time.time()
        ))
        
        await asyncio.sleep(1.2)
        
        await visualization_manager.add_agent_thought(flow_id, AgentThought(
            agent_id=agent_id,
            agent_name=agent_name,
            message="Подготовил ответ и отправляю мета-агенту",
            thought_type="responding",
            timestamp=time.time(),
            target_agent="meta_agent"
        ))
    
    await asyncio.sleep(1.0)
    
    # 6. Мета-агент собирает ответы
    await visualization_manager.update_flow_stage(flow_id, "response_generation", "meta_agent")
    await visualization_manager.add_agent_thought(flow_id, AgentThought(
        agent_id="meta_agent",
        agent_name="Мета-Агент",
        message="Получил ответы от всех агентов. Синтезирую финальный ответ...",
        thought_type="thinking",
        timestamp=time.time()
    ))
    
    await asyncio.sleep(1.5)
    
    # 7. Мета-агент отправляет коммуникатору
    await visualization_manager.add_agent_thought(flow_id, AgentThought(
        agent_id="meta_agent",
        agent_name="Мета-Агент", 
        message="Отправляю сводный ответ коммуникатору",
        thought_type="responding",
        timestamp=time.time(),
        target_agent="communicator"
    ))
    
    await asyncio.sleep(0.5)
    
    # 8. Коммуникатор финализирует ответ
    await visualization_manager.add_agent_thought(flow_id, AgentThought(
        agent_id="communicator",
        agent_name="Коммуникатор",
        message="Получил ответ от команды. Форматирую для пользователя...",
        thought_type="thinking", 
        timestamp=time.time()
    ))
    
    await asyncio.sleep(0.8)


# Chat history endpoint moved to routes_chat.py


# =============================================================================
# METRICS API - для метрик и мониторинга
# =============================================================================

@app.get("/api/v1/metrics/dashboard", response_model=SystemMetrics, dependencies=[Depends(rate_limit_dependency)])
# permissions disabled to keep compatibility
async def get_dashboard_metrics(current_user: dict | None = None):
    """Метрики для дашборда"""
    try:
        import psutil
        
        uptime = str(datetime.now(timezone.utc) - api_state.start_time)
        memory = f"{psutil.virtual_memory().percent:.1f}%"
        cpu = psutil.cpu_percent(interval=1)
        
        return SystemMetrics(
            total_messages=len(api_state.message_history),
            active_agents=(len(getattr(api_state.groupchat_manager, 'agents', {})) if api_state.groupchat_manager else 0),
            uptime=uptime,
            memory_usage=memory,
            cpu_usage=cpu
        )
        
    except ImportError:
        # Fallback если psutil не установлен
        return SystemMetrics(
            total_messages=len(api_state.message_history),
            active_agents=12 if api_state.groupchat_manager else 0,
            uptime=str(datetime.now(timezone.utc) - api_state.start_time)
        )
    except Exception as e:
        logger.error(f"❌ Ошибка получения метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/voice/stats")
async def get_voice_stats():
    """Получение статистики голосовой обработки"""
    try:
        from tools.core_voice_processor import VoiceProcessingCoordinator, AUTOGEN_CORE_AVAILABLE
        
        if not AUTOGEN_CORE_AVAILABLE:
            return JSONResponse(
                content={
                    "status": "unavailable",
                    "message": "autogen-core not installed"
                },
                status_code=503
            )
            
        # Здесь был бы доступ к глобальному voice coordinator
        # Для примера возвращаем базовую информацию
        return {
            "core_available": AUTOGEN_CORE_AVAILABLE,
            "speechkit_configured": bool(os.getenv("YANDEX_API_KEY")),
            "optimization": "autogen-core based",
            "features": [
                "Voice recognition caching",
                "Speech synthesis caching",
                "Parallel processing",
                "Low latency mode"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting voice stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Cache endpoints moved to routes_cache.py


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics(
    current_user: dict = Depends(auth_user_dependency)
) -> PlainTextResponse:
    """Экспорт Prometheus метрик, если клиент установлен."""
    # Проверяем права на чтение метрик
    role = current_user.get('role', Role.USER)
    if not check_permission(role, "metrics:read"):
        raise HTTPException(status_code=403, detail="Access denied to metrics")
    try:
        from prometheus_client import REGISTRY, generate_latest, CONTENT_TYPE_LATEST  # type: ignore
    except Exception:
        raise HTTPException(status_code=404, detail="prometheus_client not installed")
    try:
        data = generate_latest(REGISTRY)
        return PlainTextResponse(content=data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"❌ Ошибка генерации метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Agent status endpoint moved to routes_agents.py


# =============================================================================
# PROJECTS API - для управления проектами
# =============================================================================

# Projects and logs endpoints moved to routes_misc.py


# =============================================================================
# REGISTRY API (read-only + rollback)
# =============================================================================

# Registry list endpoints moved to routes_registry.py


@app.get("/api/v1/registry/instances")
async def registry_instances():
    raise HTTPException(status_code=501, detail="Instances registry not implemented")


@app.get("/api/v1/registry/tools/{name}/versions")
async def registry_tool_versions(name: str):
    return get_tool_versions(name)


@app.get("/api/v1/registry/workflows/{key}/versions")
async def registry_workflow_versions(key: str):
    return get_workflow_versions(key)


@app.get("/api/v1/registry/apps/{key}/versions")
async def registry_app_versions(key: str):
    return get_app_versions(key)


@app.get("/api/v1/registry/instances/{key}/versions")
async def registry_instance_versions(key: str):
    raise HTTPException(status_code=501, detail="Instances registry not implemented")


# Registry rollback endpoints moved to routes_registry.py


@app.post("/api/v1/registry/instances/{key}/rollback") 
async def registry_instance_rollback(
    key: str, 
    target_version: int | None = None,
    current_user: dict = Depends(auth_user_dependency)
):
    # Проверяем права администратора
    if current_user.get('role') != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Функция rollback_instance не существует в multitool, возвращаем ошибку
    raise HTTPException(status_code=501, detail="Instance rollback not implemented")
    return {"status": "ok"}


# =============================================================================
# WEBSOCKET для real-time обновлений
# =============================================================================

# WebSocket endpoints moved to routes_websocket.py


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

# Studio logs endpoint moved to routes_studio.py
        logger.error(f"❌ Ошибка получения Studio логов: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Studio logs")


# Новые endpoints для визуализации мыслительного процесса

# Agent profiles endpoint moved to routes_agents.py

# Visualization flows endpoint moved to routes_studio.py

# Visualization WebSocket moved to routes_websocket.py


# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with proper logging"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Don't expose internal errors in production
    if os.getenv('DEBUG', '').lower() == 'true':
        detail = str(exc)
    else:
        detail = "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={"detail": detail, "type": type(exc).__name__}
    )


# Federation endpoints
if FEDERATION_ENABLED:
    @app.get("/api/v1/federation/status",
             dependencies=[Depends(rate_limit_dependency)])
    async def get_federation_status():
        """Получить статус федерации"""
        return federation_hub.get_federation_status()
    
    @app.post("/api/v1/federation/join",
              dependencies=[Depends(rate_limit_dependency)])
    async def join_federation(hub_endpoint: str, specialization: List[str]):
        """Присоединиться к федерации"""
        success = await federation_hub.join_federation(hub_endpoint, specialization)
        return {"success": success}
    
    @app.post("/api/v1/federation/sync",
              dependencies=[Depends(rate_limit_dependency)])
    async def sync_federation():
        """Синхронизироваться с федерацией"""
        stats = await federation_hub.sync_with_federation()
        return stats
    
    @app.post("/federation/receive_knowledge")
    async def receive_knowledge(packet: Dict[str, Any]):
        """Получить знания от другого узла"""
        # Store in cache
        federation_hub.knowledge_cache[packet["packet_id"]] = packet
        return {"status": "received"}
    
    @app.post("/federation/request_knowledge")
    async def handle_knowledge_request(request: Dict[str, Any]):
        """Обработать запрос знаний от другого узла"""
        # Prepare knowledge packets based on request
        packets = federation_hub.prepare_knowledge_for_sharing(
            request.get("knowledge_domain", "general")
        )
        return [p.__dict__ for p in packets[:10]]  # Limit response


# Auth endpoints moved to routes_auth.py


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
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )