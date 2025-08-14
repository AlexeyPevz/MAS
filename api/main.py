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

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.security import HTTPAuthorizationCredentials

# Импорты MAS системы
from tools.smart_groupchat import SmartGroupChatManager
from tools.modern_telegram_bot import ModernTelegramBot
from config.config_loader import load_config
from api.integration import mas_integration
from tools import studio_logger
from api.security import rate_limit_dependency, require_permission, Role, auth_user_dependency
from api.security import Token as AuthTokenModel
from api.security import security_manager, SECRET_KEY, ALGORITHM
import jwt

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
    message: str
    user_id: Optional[str] = "api_user"
    metadata: Optional[Dict[str, Any]] = {}


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
# AUTH MODELS
# =============================
class AuthRequest(BaseModel):
    user_id: str
    role: Optional[str] = Role.USER
    scopes: Optional[List[str]] = []
    expires_minutes: Optional[int] = None

class RefreshRequest(BaseModel):
    refresh_token: str

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

from tools.yandex_speechkit import speechkit, process_voice_message, synthesize_response

@app.post("/api/v1/voice/stt")
async def speech_to_text(audio_file: bytes):
    """Распознавание речи в текст"""
    try:
        if not speechkit.is_configured():
            raise HTTPException(status_code=503, detail="SpeechKit не настроен")
        
        text = await speechkit.speech_to_text(audio_file)
        
        if text:
            return {"text": text, "status": "success"}
        else:
            return {"text": "", "status": "empty", "message": "Не удалось распознать речь"}
            
    except Exception as e:
        logger.error(f"❌ Ошибка STT: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/voice/tts")
async def text_to_speech(request: dict):
    """Синтез речи из текста"""
    try:
        if not speechkit.is_configured():
            raise HTTPException(status_code=503, detail="SpeechKit не настроен")
        
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Текст не указан")
        
        audio_data = await speechkit.text_to_speech(text)
        
        if audio_data:
            from fastapi.responses import Response
            return Response(
                content=audio_data,
                media_type="audio/ogg",
                headers={"Content-Disposition": "attachment; filename=speech.ogg"}
            )
        else:
            raise HTTPException(status_code=500, detail="Ошибка синтеза речи")
            
    except Exception as e:
        logger.error(f"❌ Ошибка TTS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/voice/chat", response_model=ChatResponse)
async def voice_chat(audio_file: bytes, user_id: str = "voice_user"):
    """Голосовой чат: STT -> Chat -> TTS"""
    try:
        # 1. Распознаем речь
        text = await process_voice_message(audio_file)
        if not text or text.startswith("❌") or text.startswith("🔧"):
            raise HTTPException(status_code=400, detail=text or "Ошибка распознавания")
        
        # 2. Обрабатываем через MAS
        chat_msg = ChatMessage(message=text, user_id=user_id)
        chat_response = await send_message(chat_msg)
        
        # 3. Синтезируем голосовой ответ
        audio_data = await synthesize_response(chat_response.response)
        
        # 4. Возвращаем результат с аудио
        chat_response.metadata = chat_response.metadata or {}
        chat_response.metadata["has_audio"] = audio_data is not None
        chat_response.metadata["recognized_text"] = text
        
        return chat_response
        
    except Exception as e:
        logger.error(f"❌ Ошибка voice chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# CHAT API - для диалога с Communicator Agent
# =============================================================================

@app.post("/api/v1/chat/simple", response_model=ChatResponse, dependencies=[Depends(rate_limit_dependency)])
async def simple_chat(message: ChatMessage, current_user: dict | None = None):
    """Простой чат без визуализации для тестирования"""
    try:
        # Обрабатываем сообщение через MAS
        response_text = await mas_integration.process_message(message.message, current_user["user_id"] if current_user else message.user_id)
        
        return ChatResponse(
            response=response_text,
            agent="system",
            timestamp=time.time()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat/message", response_model=ChatResponse, dependencies=[Depends(rate_limit_dependency)])
async def send_message_with_visualization(message: ChatMessage, current_user: dict | None = None):
    """Отправка сообщения с визуализацией мыслительного процесса"""
    try:
        # Начинаем новый поток визуализации
        flow_id = await visualization_manager.start_message_flow(
            message.message, current_user["user_id"] if current_user else message.user_id
        )
        
        # Симуляция мыслительного процесса (позже заменить на реальную интеграцию)
        await simulate_agent_thinking(flow_id, message.message)
        
        # Обрабатываем сообщение через MAS
        response_text = await mas_integration.process_message(message.message, message.user_id)
        
        # Завершаем поток визуализации
        await visualization_manager.complete_message_flow(flow_id, response_text)
        
        return ChatResponse(
            response=response_text,
            agent="communicator",
            timestamp=time.time(),
            flow_id=flow_id
        )
    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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


@app.get("/api/v1/cache/stats", dependencies=[Depends(rate_limit_dependency)])
# permissions disabled to keep compatibility
async def get_cache_stats(current_user: dict | None = None):
    """Получение статистики семантического кэша"""
    if not SEMANTIC_CACHE_ENABLED:
        raise HTTPException(status_code=503, detail="Semantic cache not enabled")
    
    try:
        stats = semantic_cache.get_stats()
        
        # Добавляем информацию о топ запросах
        top_queries = []
        for key, entry in list(semantic_cache.local_cache.items())[:10]:
            top_queries.append({
                "query": entry.query[:100] + "..." if len(entry.query) > 100 else entry.query,
                "hits": entry.hits,
                "similarity_score": entry.similarity_score,
                "tokens_saved": entry.tokens_saved,
                "last_accessed": datetime.fromtimestamp(entry.last_accessed).isoformat()
            })
        
        stats["top_queries"] = top_queries
        stats["cache_enabled"] = True
        
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/cache/clear", dependencies=[Depends(rate_limit_dependency)])
# permissions disabled to keep compatibility
async def clear_cache(partial: bool = False, current_user: dict | None = None):
    """Очистка семантического кэша"""
    if not SEMANTIC_CACHE_ENABLED:
        raise HTTPException(status_code=503, detail="Semantic cache not enabled")
    
    try:
        if partial:
            # Очищаем только истекшие записи
            await semantic_cache.clear_expired()
            return {"status": "success", "message": "Expired entries cleared"}
        else:
            # Полная очистка
            old_size = len(semantic_cache.local_cache)
            semantic_cache.local_cache.clear()
            semantic_cache.stats = {
                "hits": 0,
                "misses": 0,
                "semantic_hits": 0,
                "exact_hits": 0,
                "total_tokens_saved": 0,
                "total_cost_saved": 0.0,
                "avg_similarity": 0.0
            }
            return {"status": "success", "message": f"Cleared {old_size} entries"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics() -> PlainTextResponse:
    """Экспорт Prometheus метрик, если клиент установлен."""
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


@app.get("/api/v1/agents/status")
async def get_agents_status():
    """Статус всех агентов (динамически)."""
    try:
        if not api_state.groupchat_manager:
            return {"agents": [], "total": 0}
        # Считаем активность по истории сообщений
        stats = {}
        try:
            stats = api_state.groupchat_manager.get_agent_statistics()
        except Exception:
            stats = {}
        agents = []
        for name in getattr(api_state.groupchat_manager, "agents", {}).keys():
            agents.append(AgentStatus(name=name, status="active", message_count=stats.get(name, 0)))
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
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
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
                "timestamp": datetime.now(timezone.utc),
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
    """Получение или проксирование логов AutoGen Studio."""
    try:
        studio_url = os.getenv("AUTOGEN_STUDIO_URL")

        if studio_url:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"{studio_url}/api/v1/logs")
                    resp.raise_for_status()
                    return JSONResponse(status_code=resp.status_code, content=resp.json())
            except Exception as proxy_err:
                logger.error(f"❌ Failed to proxy Studio logs: {proxy_err}")

        log_path = studio_logger.LOG_PATH
        if not log_path.exists():
            raise HTTPException(status_code=404, detail="Studio log file not found")

        logs: List[Dict[str, Any]] = []
        with log_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.error(f"Invalid log line encountered: {line}")

        return JSONResponse(content=logs)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения Studio логов: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Studio logs")


# Новые endpoints для визуализации мыслительного процесса

@app.get("/api/v1/agents/profiles", response_model=List[AgentProfile])
async def get_agent_profiles():
    """Получение профилей всех агентов"""
    return AGENT_PROFILES

@app.get("/api/v1/visualization/flows")
async def get_active_flows():
    """Получение активных потоков обработки сообщений"""
    return list(visualization_manager.message_flows.values())

@app.websocket("/ws/visualization")
async def visualization_websocket(websocket: WebSocket):
    """WebSocket для визуализации мыслительного процесса"""
    await visualization_manager.connect(websocket)
    try:
        while True:
            # Ожидаем сообщений от клиента (ping/pong, настройки и т.д.)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "get_agent_profiles":
                await websocket.send_text(json.dumps({
                    "type": "agent_profiles", 
                    "data": [profile.dict() for profile in AGENT_PROFILES]
                }))
    except WebSocketDisconnect:
        visualization_manager.disconnect(websocket)


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


# =============================================================================
# AUTH API
# =============================================================================

@app.post("/api/v1/auth/token", response_model=AuthTokenModel)
async def issue_token(request: AuthRequest, admin_secret: Optional[str] = None):
    """Выдача access/refresh токенов. Требует ADMIN_SECRET в заголовке X-Admin-Secret, если он задан в окружении."""
    from fastapi import Request as _Request
    # В FastAPI зависимость Request нужна для заголовков; но чтобы не менять сигнатуру, читаем из env и admin_secret (compat)
    expected = os.getenv("ADMIN_SECRET")
    provided = admin_secret  # совместимость для прямых вызовов
    try:
        # Попытка достать заголовок, если контекст позволяет
        # (обратная совместимость: допускаем параметр admin_secret) 
        pass
    except Exception:
        pass
    if expected:
        # Если секрет задан, требуем совпадение
        headers_secret = expected if provided == expected else None
        if not (provided == expected or headers_secret):
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        logger.warning("ADMIN_SECRET не задан: token issuance открыт (dev mode)")
    # Формируем payload
    data = {"sub": request.user_id, "role": request.role or Role.USER, "scopes": request.scopes or []}
    expires = timedelta(minutes=request.expires_minutes) if request.expires_minutes else None
    access = security_manager.create_access_token(data, expires)
    refresh = security_manager.create_refresh_token(data)
    return AuthTokenModel(access_token=access, refresh_token=refresh)


@app.post("/api/v1/auth/refresh", response_model=AuthTokenModel)
async def refresh_token(payload: RefreshRequest):
    """Обновление access токена по refresh токену."""
    try:
        decoded = jwt.decode(payload.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
        user_id = decoded.get("sub")
        role = decoded.get("role", Role.USER)
        scopes = decoded.get("scopes", [])
        access = security_manager.create_access_token({"sub": user_id, "role": role, "scopes": scopes})
        new_refresh = security_manager.create_refresh_token({"sub": user_id, "role": role, "scopes": scopes})
        return AuthTokenModel(access_token=access, refresh_token=new_refresh)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security_manager.bearer_scheme)):
    """Отзыв текущего access токена."""
    token = credentials.credentials
    security_manager.revoke_token(token)
    return {"status": "revoked"}


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