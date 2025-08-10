"""
Event Sourcing System for Root-MAS
Система записи всех событий для аудита и воспроизведения состояния
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
import json
import asyncio
from pathlib import Path
import uuid
from enum import Enum


class EventType(Enum):
    """Типы событий в системе"""
    # Agent events
    AGENT_CREATED = "agent_created"
    AGENT_MESSAGE_RECEIVED = "agent_message_received"
    AGENT_MESSAGE_SENT = "agent_message_sent"
    AGENT_TASK_STARTED = "agent_task_started"
    AGENT_TASK_COMPLETED = "agent_task_completed"
    AGENT_TASK_FAILED = "agent_task_failed"
    AGENT_KNOWLEDGE_REQUEST = "agent_knowledge_request"
    AGENT_KNOWLEDGE_UPDATED = "agent_knowledge_updated"
    
    # System events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    MODEL_TIER_CHANGED = "model_tier_changed"
    BUDGET_THRESHOLD_REACHED = "budget_threshold_reached"
    
    # User events
    USER_MESSAGE_RECEIVED = "user_message_received"
    USER_FEEDBACK_PROVIDED = "user_feedback_provided"
    
    # Prompt events
    PROMPT_CREATED = "prompt_created"
    PROMPT_UPDATED = "prompt_updated"
    PROMPT_DELETED = "prompt_deleted"
    
    # Memory events
    MEMORY_STORED = "memory_stored"
    MEMORY_RETRIEVED = "memory_retrieved"
    MEMORY_SEARCH = "memory_search"


@dataclass
class Event:
    """Базовое событие системы"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.SYSTEM_STARTED
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_id: Optional[str] = None  # ID сущности к которой относится событие
    actor: Optional[str] = None  # Кто инициировал событие
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для сериализации"""
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "aggregate_id": self.aggregate_id,
            "actor": self.actor,
            "data": self.data,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Создание из словаря"""
        return cls(
            id=data["id"],
            type=EventType(data["type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            aggregate_id=data.get("aggregate_id"),
            actor=data.get("actor"),
            data=data.get("data", {}),
            metadata=data.get("metadata", {})
        )


class EventStore:
    """Хранилище событий с поддержкой подписок"""
    
    def __init__(self, storage_path: str = "/workspace/data/events"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.events: List[Event] = []
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_file = self.storage_path / f"events_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"
        
        # Load existing events for today
        self._load_today_events()
    
    async def append(self, event: Event) -> None:
        """Добавить событие в хранилище"""
        # Store in memory
        self.events.append(event)
        
        # Persist to file
        with open(self.event_file, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")
        
        # Notify subscribers
        await self._notify_subscribers(event)
    
    def get_events(
        self, 
        event_type: Optional[EventType] = None,
        aggregate_id: Optional[str] = None,
        actor: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Event]:
        """Получить события по фильтрам"""
        filtered = self.events
        
        if event_type:
            filtered = [e for e in filtered if e.type == event_type]
        
        if aggregate_id:
            filtered = [e for e in filtered if e.aggregate_id == aggregate_id]
        
        if actor:
            filtered = [e for e in filtered if e.actor == actor]
        
        if start_time:
            filtered = [e for e in filtered if e.timestamp >= start_time]
        
        if end_time:
            filtered = [e for e in filtered if e.timestamp <= end_time]
        
        return filtered[-limit:]
    
    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """Подписаться на события определенного типа"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """Отписаться от событий"""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(callback)
    
    async def _notify_subscribers(self, event: Event) -> None:
        """Уведомить подписчиков о событии"""
        callbacks = self.subscribers.get(event.type, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"Error in event subscriber: {e}")
    
    def _load_today_events(self) -> None:
        """Загрузить события за сегодня"""
        if self.event_file.exists():
            with open(self.event_file, "r") as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        self.events.append(Event.from_dict(event_data))
                    except Exception as e:
                        print(f"Error loading event: {e}")
    
    def get_aggregate_history(self, aggregate_id: str) -> List[Event]:
        """Получить полную историю событий для агрегата"""
        return [e for e in self.events if e.aggregate_id == aggregate_id]
    
    def replay_events(
        self, 
        events: List[Event], 
        handler: Callable[[Event], None]
    ) -> None:
        """Воспроизвести события через обработчик"""
        for event in sorted(events, key=lambda e: e.timestamp):
            handler(event)
    
    def create_snapshot(self, aggregate_id: str) -> Dict[str, Any]:
        """Создать снимок состояния на основе событий"""
        events = self.get_aggregate_history(aggregate_id)
        
        # Build state from events
        state = {
            "aggregate_id": aggregate_id,
            "last_event_id": events[-1].id if events else None,
            "event_count": len(events),
            "created_at": events[0].timestamp if events else None,
            "updated_at": events[-1].timestamp if events else None,
            "current_state": self._build_state_from_events(events)
        }
        
        return state
    
    def _build_state_from_events(self, events: List[Event]) -> Dict[str, Any]:
        """Построить текущее состояние из событий"""
        state = {}
        
        for event in events:
            # Apply event to state based on type
            if event.type == EventType.AGENT_CREATED:
                state["status"] = "created"
                state.update(event.data)
            
            elif event.type == EventType.AGENT_TASK_STARTED:
                state["current_task"] = event.data.get("task_id")
                state["status"] = "busy"
            
            elif event.type == EventType.AGENT_TASK_COMPLETED:
                state["last_task"] = event.data.get("task_id")
                state["status"] = "idle"
                state["completed_tasks"] = state.get("completed_tasks", 0) + 1
            
            elif event.type == EventType.AGENT_TASK_FAILED:
                state["last_error"] = event.data.get("error")
                state["status"] = "error"
                state["failed_tasks"] = state.get("failed_tasks", 0) + 1
            
            # Add more event handlers as needed
        
        return state


class EventLogger:
    """Удобный интерфейс для логирования событий"""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    async def log_agent_message(
        self, 
        agent_name: str, 
        message_type: str,
        content: str,
        direction: str = "received",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Логировать сообщение агента"""
        event_type = (
            EventType.AGENT_MESSAGE_RECEIVED 
            if direction == "received" 
            else EventType.AGENT_MESSAGE_SENT
        )
        
        event = Event(
            type=event_type,
            aggregate_id=agent_name,
            actor=agent_name,
            data={
                "message_type": message_type,
                "content": content[:1000],  # Limit content size
                "direction": direction
            },
            metadata=metadata or {}
        )
        
        await self.event_store.append(event)
    
    async def log_task_lifecycle(
        self,
        task_id: str,
        agent_name: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Логировать жизненный цикл задачи"""
        event_type_map = {
            "started": EventType.AGENT_TASK_STARTED,
            "completed": EventType.AGENT_TASK_COMPLETED,
            "failed": EventType.AGENT_TASK_FAILED
        }
        
        event_type = event_type_map.get(status, EventType.AGENT_TASK_STARTED)
        
        event = Event(
            type=event_type,
            aggregate_id=task_id,
            actor=agent_name,
            data={
                "task_id": task_id,
                "agent_name": agent_name,
                "status": status,
                **(details or {})
            }
        )
        
        await self.event_store.append(event)
    
    async def log_knowledge_operation(
        self,
        agent_name: str,
        operation: str,
        topic: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Логировать операции с базой знаний"""
        event_type = (
            EventType.AGENT_KNOWLEDGE_REQUEST 
            if operation == "request" 
            else EventType.AGENT_KNOWLEDGE_UPDATED
        )
        
        event = Event(
            type=event_type,
            aggregate_id=agent_name,
            actor=agent_name,
            data={
                "operation": operation,
                "topic": topic,
                "success": success,
                **(details or {})
            }
        )
        
        await self.event_store.append(event)
    
    async def log_system_event(
        self,
        event_type: EventType,
        details: Dict[str, Any],
        actor: Optional[str] = None
    ) -> None:
        """Логировать системное событие"""
        event = Event(
            type=event_type,
            actor=actor or "system",
            data=details
        )
        
        await self.event_store.append(event)


# Global instances
event_store = EventStore()
event_logger = EventLogger(event_store)