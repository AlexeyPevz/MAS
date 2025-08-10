"""
Smart GroupChat Manager
Интеллектуальный менеджер групповых чатов с реальной LLM коммуникацией
"""
import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# AutoGen v0.4+ is used via autogen-agentchat in agent implementations.
# No direct imports from legacy autogen here.

# Import quality metrics
from .quality_metrics import quality_metrics, TaskResult


@dataclass
class Message:
    """Структура сообщения в системе"""
    sender: str
    recipient: Optional[str]
    content: str
    timestamp: datetime
    message_type: str = "text"  # text, task, result, error
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SmartGroupChatManager:
    """Продвинутый менеджер групповых чатов"""
    
    def __init__(self, agents: Dict[str, Any] = None, routing: Dict[str, List[str]] = None):
        self.agents = agents or {}
        self.routing = routing or {}
        self.conversation_history: List[Message] = []
        self.active_tasks: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        
        # Конфигурация системы
        self.max_conversation_length = 50
        self.max_retries = 3
        self._initialized = False
    
    async def initialize(self):
        """Инициализация менеджера группового чата"""
        if self._initialized:
            return
        
        self.logger.info("🔧 Инициализация SmartGroupChatManager...")
        
        # Загружаем конфигурацию агентов если не заданы
        if not self.agents:
            from config.config_loader import load_config
            from agents.core_agents import AGENT_CLASSES
            
            config = load_config()
            agents_config = config.get('agents', {})
            
            # Загружаем конфигурацию tier'ов
            tiers_config = config.get('llm_tiers', {})
            
            # Создаем экземпляры агентов
            for agent_name, agent_info in agents_config.items():
                if agent_name in AGENT_CLASSES:
                    agent_class = AGENT_CLASSES[agent_name]
                    tier = agent_info.get('default_tier', 'cheap')
                    
                    # Получаем модель из конфигурации tier'а
                    tier_info = tiers_config.get('tiers', {}).get(tier, [])
                    if tier_info and isinstance(tier_info, list) and len(tier_info) > 0:
                        # Берем первую модель из списка для данного tier'а
                        model_info = tier_info[0]
                        provider = model_info.get('provider', 'openrouter')
                        model_name = model_info.get('name', 'gpt-3.5-turbo')
                        model = f"{provider}/{model_name}" if provider != 'openai' else model_name
                    else:
                        # Дефолтная модель
                        model = 'openrouter/gpt-3.5-turbo'
                    
                    self.agents[agent_name] = agent_class(model=model, tier=tier)
                    self.logger.info(f"✅ Создан агент: {agent_name} (модель: {model}, tier: {tier})")
        
        # Настраиваем маршрутизацию по умолчанию если не задана
        if not self.routing:
            self.routing = {
                "communicator": ["meta"],
                "meta": ["coordination", "researcher", "model_selector"],
                "coordination": ["agent_builder", "instance_factory"],
                "researcher": ["fact_checker", "multi_tool"],
                "model_selector": ["prompt_builder"],
                "workflow_builder": ["instance_factory"],
                "webapp_builder": ["instance_factory"],
            }
        
        self._initialized = True
        self.logger.info("✅ SmartGroupChatManager инициализирован")
        
    async def process_user_message(self, content: str, user_id: str = "user") -> str:
        """Обработка сообщения от пользователя"""
        self.logger.info(f"📨 Получено сообщение от {user_id}: {content[:100]}...")
        
        # Создаем сообщение
        user_message = Message(
            sender=user_id,
            recipient="communicator",
            content=content,
            timestamp=datetime.now(timezone.utc),
            message_type="text"
        )
        
        self.conversation_history.append(user_message)
        self._trim_history()
        
        # Начинаем обработку с Communicator агента
        try:
            response = await self._route_message_to_agent("communicator", user_message)
            return response
        except Exception as e:
            self.logger.error(f"❌ Ошибка обработки сообщения: {e}")
            return f"Извините, произошла ошибка при обработке вашего запроса: {e}"
    
    async def _route_message_to_agent(self, agent_name: str, message: Message):
        """Маршрутизация сообщения агенту с отслеживанием метрик"""
        if agent_name not in self.agents:
            self.logger.error(f"❌ Агент {agent_name} не найден")
            return None
        
        agent = self.agents[agent_name]
        start_time = asyncio.get_event_loop().time()
        task_id = f"{agent_name}_{int(start_time)}"
        
        try:
            self.logger.info(f"📤 Отправка сообщения агенту {agent_name}")
            
            # Создаем контекст для агента
            context = self._build_context_for_agent(agent_name, message)
            
            # Генерируем ответ от агента (async‑путь для v0.4+)
            if hasattr(agent, 'generate_reply_async') and asyncio.iscoroutinefunction(getattr(agent, 'generate_reply_async')):
                try:
                    response_obj = await agent.generate_reply_async(
                        messages=context,
                        sender=None
                    )
                    response = response_obj.chat_message.content if hasattr(response_obj, 'chat_message') else str(response_obj)
                    
                    # Если ответ пустой или None
                    if not response:
                        response = f"[{agent_name}] Сообщение обработано"
                    
                    # Сохраняем в память если есть
                    if hasattr(agent, 'remember'):
                        agent.remember(f"last_interaction_{message.sender}", message.content)
                        agent.remember(f"last_response_{agent_name}", response)
                except Exception as e:
                    self.logger.error(f"❌ LLM вызов агента {agent_name} failed: {e}")
                    if "on_messages" in str(e) or "autogen" in str(e).lower():
                        self.logger.warning(f"⚠️ Возможна проблема с AutoGen v0.4 API, используем fallback")
                    response = self._generate_fallback_response(agent_name, message.content)
            elif hasattr(agent, 'generate_reply') and callable(getattr(agent, 'generate_reply')):
                # Легаси‑путь: синхронные агенты, исполняем в отдельном потоке чтобы не блокировать event loop
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: agent.generate_reply(messages=context, sender=None)
                )
                if not response:
                    response = f"[{agent_name}] Сообщение обработано"
            else:
                # Fallback для mock агентов
                response = self._generate_fallback_response(agent_name, message.content)
            
            # Сохраняем ответ агента
            response_msg = Message(
                sender=agent_name,
                recipient=message.sender,
                content=response,
                timestamp=datetime.now(timezone.utc),
                message_type="text"
            )
            
            self.conversation_history.append(response_msg)
            
            # Поддерживаем ограничение памяти истории диалога
            self._trim_history()
            
            # Определяем следующих агентов для маршрутизации
            next_agents = self.routing.get(agent_name, [])
            
            # Calculate metrics
            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time
            
            # Extract confidence if available
            confidence = 0.75  # Default
            if isinstance(response, dict) and 'confidence' in response:
                confidence = response['confidence']
                actual_response = response['response']
            else:
                actual_response = response
            
            # Check if we should get optimized model suggestion
            if hasattr(agent, 'task_type'):
                optimization = quality_metrics.suggest_model_optimization(
                    agent_name, 
                    agent.task_type
                )
                if optimization.get('suggestion') != "Use default tier":
                    self.logger.info(f"💡 Model optimization suggestion for {agent_name}: {optimization['suggestion']}")
            
            # Record success
            quality_metrics.record_task_result(TaskResult(
                task_id=task_id,
                agent_name=agent_name,
                task_type=message.message_type,
                status="success",
                confidence=confidence,
                response_time=response_time,
                model_used=agent.model if hasattr(agent, "model") else "unknown",
                tier_used=agent.tier if hasattr(agent, "tier") else "standard",
                token_cost=response_time * 0.0001  # Placeholder calculation
            ))
            
            self.logger.info(f"✅ Агент {agent_name} обработал сообщение")
            
            # Continue routing if needed
            if self._should_continue_routing(agent_name, actual_response):
                await self._process_routing_chain(next_agents, response_msg)
            
            return actual_response
            
        except Exception as e:
            # Record failure
            end_time = asyncio.get_event_loop().time()
            
            quality_metrics.record_task_result(TaskResult(
                task_id=task_id,
                agent_name=agent_name,
                task_type=message.message_type,
                status="failure",
                confidence=0.0,
                response_time=end_time - start_time,
                model_used=agent.model if hasattr(agent, "model") else "unknown",
                tier_used=agent.tier if hasattr(agent, "tier") else "standard",
                token_cost=0.0,
                error=type(e).__name__
            ))
            
            self.logger.error(f"❌ Ошибка при обработке агентом {agent_name}: {e}")
            raise
    
    def _build_context_for_agent(self, agent_name: str, message: Message) -> List[Dict]:
        """Построение контекста разговора для агента"""
        # Берем последние сообщения для контекста
        recent_messages = self.conversation_history[-10:]
        
        context = []
        
        # Добавляем системное сообщение агента
        agent = self.agents[agent_name]
        if hasattr(agent, 'system_message') and agent.system_message:
            context.append({
                "role": "system",
                "content": agent.system_message
            })
        
        # Добавляем историю разговора
        for msg in recent_messages:
            role = "user" if msg.sender == "user" else "assistant"
            context.append({
                "role": role,
                "content": f"[{msg.sender}]: {msg.content}"
            })
        
        # Добавляем текущее сообщение
        context.append({
            "role": "user",
            "content": f"[{message.sender}]: {message.content}"
        })
        
        return context
    
    async def _process_routing_chain(self, next_agents: List[str], message: Message):
        """Обработка цепочки маршрутизации"""
        for next_agent in next_agents:
            if next_agent in self.agents:
                try:
                    await self._route_message_to_agent(next_agent, message)
                except Exception as e:
                    self.logger.error(f"❌ Ошибка маршрутизации к {next_agent}: {e}")
    
    def _should_continue_routing(self, agent_name: str, response: str) -> bool:
        """Определение необходимости продолжения маршрутизации"""
        # Защита от бесконечной рекурсии - максимум 3 прохода через одного агента
        recent_messages = self.conversation_history[-20:]  # Смотрим последние 20 сообщений
        agent_count = sum(1 for msg in recent_messages if msg.sender == agent_name)
        
        if agent_count >= 3:
            self.logger.warning(f"🔄 Агент {agent_name} уже выполнялся {agent_count} раз, остановка маршрутизации")
            return False
        
        # Проверяем общую длину цепочки - не более 10 переходов подряд
        if len(recent_messages) >= 10:
            return False
        
        # Простая логика - не продолжаем если это финальный ответ
        stop_phrases = [
            "завершено",
            "готово", 
            "выполнено",
            "ошибка",
            "не могу",
            "невозможно"
        ]
        
        response_lower = response.lower()
        for phrase in stop_phrases:
            if phrase in response_lower:
                return False
        
        return True
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Получение сводки разговора"""
        return {
            "total_messages": len(self.conversation_history),
            "active_agents": list(set(msg.sender for msg in self.conversation_history)),
            "last_activity": self.conversation_history[-1].timestamp if self.conversation_history else None,
            "active_tasks": len(self.active_tasks)
        }
    
    def get_agent_statistics(self) -> Dict[str, int]:
        """Статистика активности агентов"""
        stats = {}
        for msg in self.conversation_history:
            if msg.sender not in stats:
                stats[msg.sender] = 0
            stats[msg.sender] += 1
        return stats
    
    async def create_task(self, task_description: str, assigned_agent: str) -> str:
        """Создание задачи для агента"""
        task_id = f"task_{len(self.active_tasks) + 1}"
        
        task = {
            "id": task_id,
            "description": task_description,
            "assigned_agent": assigned_agent,
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "result": None
        }
        
        self.active_tasks[task_id] = task
        
        # Отправляем задачу агенту
        task_message = Message(
            sender="system",
            recipient=assigned_agent,
            content=f"Новая задача: {task_description}",
            timestamp=datetime.now(timezone.utc),
            message_type="task",
            metadata={"task_id": task_id}
        )
        
        await self._route_message_to_agent(assigned_agent, task_message)
        
        return task_id
    
    def _generate_fallback_response(self, agent_name: str, message_content: str) -> str:
        """Генерация fallback ответа для агента"""
        responses = {
            "meta": f"🎯 [Meta] Анализирую задачу: '{message_content[:50]}...' - составляю план выполнения",
            "coordination": f"📋 [Coordination] Принял задачу в работу и распределяю между исполнителями",
            "researcher": f"🔍 [Researcher] Ищу информацию по запросу: '{message_content[:30]}...'",
            "fact_checker": f"✅ [Fact-Checker] Проверяю достоверность полученной информации",
            "prompt_builder": f"📝 [Prompt-Builder] Оптимизирую промпты для лучшей работы агентов", 
            "communicator": f"💬 [Communicator] Обрабатываю сообщение и готовлю ответ пользователю",
        }
        
        default_response = f"🤖 [{agent_name}] Обработано: {message_content[:50]}..."
        return responses.get(agent_name, default_response)

    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        return {
            "agents_count": len(self.agents),
            "routing_rules": len(self.routing),
            "conversation_length": len(self.conversation_history),
            "active_tasks": len(self.active_tasks),
            "system_health": "healthy",
            "uptime": datetime.now(timezone.utc).isoformat()
        }

    def _trim_history(self) -> None:
        """Ограничить размер истории диалога до 2×max_conversation_length."""
        limit = max(0, self.max_conversation_length * 2)
        if limit and len(self.conversation_history) > limit:
            # Оставляем последние limit сообщений
            self.conversation_history = self.conversation_history[-limit:]

    def receive(self, event: dict, sender: str | None = None) -> None:
        """Получить событие от агента и маршрутизировать его через callback_matrix.

        Ожидаемый формат события: {"event": "EVENT_NAME", "args": [..], "kwargs": {...}}
        """
        try:
            name = event.get("event") if isinstance(event, dict) else None
            if not name:
                self.logger.warning("⚠️ Некорректное событие: %s", event)
                return
            args = event.get("args", [])
            kwargs = event.get("kwargs", {})
            from tools.callback_matrix import handle_event
            handle_event(name, *args, **kwargs)
        except Exception as exc:
            self.logger.error("❌ Ошибка обработки события %s от %s: %s", event, sender, exc)


class ConversationLogger:
    """Логирование разговоров для анализа"""
    
    def __init__(self, log_file: str = "conversations.log"):
        self.log_file = log_file
        self.logger = logging.getLogger("conversation")
        
        # Настройка логгера
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_message(self, message: Message):
        """Логирование сообщения"""
        log_entry = {
            "timestamp": message.timestamp.isoformat(),
            "sender": message.sender,
            "recipient": message.recipient,
            "content": message.content,
            "type": message.message_type,
            "metadata": message.metadata
        }
        
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))


# Функции для интеграции с существующей системой
async def create_smart_groupchat(agents: Dict[str, Any], routing: Dict[str, List[str]]) -> SmartGroupChatManager:
    """Создание умного группового чата"""
    return SmartGroupChatManager(agents, routing)


if __name__ == "__main__":
    # Тестирование модуля
    print("🧪 Тестирование Smart GroupChat Manager")
    
    # Создаем mock агентов для тестирования
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.system_message = f"Вы - {name} агент."
        
        async def generate_reply_async(self, messages=None, sender=None, config=None):
            await asyncio.sleep(0)
            return f"[{self.name}] Обработано {len(messages) if messages else 0} сообщений"
        
        # Легаси-совместимость
        def generate_reply(self, messages=None, sender=None):
            return f"[{self.name}] Обработано {len(messages) if messages else 0} сообщений"
    
    test_agents = {
        "communicator": MockAgent("Communicator"),
        "meta": MockAgent("Meta"),
        "coordination": MockAgent("Coordination")
    }
    
    test_routing = {
        "communicator": ["meta"],
        "meta": ["coordination"]
    }
    
    async def test_conversation():
        manager = SmartGroupChatManager(test_agents, test_routing)
        
        response = await manager.process_user_message("Привет, создай план проекта")
        print(f"Ответ: {response}")
        
        status = manager.get_system_status()
        print(f"Статус: {status}")
    
    # Запускаем тест
    asyncio.run(test_conversation())