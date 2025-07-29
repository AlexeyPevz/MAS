"""
Smart GroupChat Manager
Интеллектуальный менеджер групповых чатов с реальной LLM коммуникацией
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


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
    
    def __init__(self, agents: Dict[str, Any], routing: Dict[str, List[str]]):
        self.agents = agents
        self.routing = routing
        self.conversation_history: List[Message] = []
        self.active_tasks: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        
        # Конфигурация системы
        self.max_conversation_length = 50
        self.max_retries = 3
        
    async def process_user_message(self, content: str, user_id: str = "user") -> str:
        """Обработка сообщения от пользователя"""
        self.logger.info(f"📨 Получено сообщение от {user_id}: {content[:100]}...")
        
        # Создаем сообщение
        user_message = Message(
            sender=user_id,
            recipient="communicator",
            content=content,
            timestamp=datetime.now(),
            message_type="text"
        )
        
        self.conversation_history.append(user_message)
        
        # Начинаем обработку с Communicator агента
        try:
            response = await self._route_message_to_agent("communicator", user_message)
            return response
        except Exception as e:
            self.logger.error(f"❌ Ошибка обработки сообщения: {e}")
            return f"Извините, произошла ошибка при обработке вашего запроса: {e}"
    
    async def _route_message_to_agent(self, agent_name: str, message: Message) -> str:
        """Маршрутизация сообщения к конкретному агенту"""
        if agent_name not in self.agents:
            return f"❌ Агент {agent_name} не найден"
        
        agent = self.agents[agent_name]
        self.logger.info(f"📡 Маршрутизация к агенту: {agent_name}")
        
        try:
            # Создаем контекст для агента
            context = self._build_context_for_agent(agent_name, message)
            
            # Генерируем ответ от агента
            if hasattr(agent, 'generate_reply') and callable(agent.generate_reply):
                # Реальный AutoGen агент
                response = agent.generate_reply(
                    messages=context,
                    sender=None
                )
            else:
                # Fallback для mock агентов
                response = f"[{agent_name}] Обработано сообщение: {message.content[:50]}..."
            
            # Сохраняем ответ агента
            agent_message = Message(
                sender=agent_name,
                recipient=message.sender,
                content=response,
                timestamp=datetime.now(),
                message_type="text"
            )
            
            self.conversation_history.append(agent_message)
            
            # Определяем следующих агентов для маршрутизации
            next_agents = self.routing.get(agent_name, [])
            
            if next_agents and self._should_continue_routing(agent_name, response):
                # Продолжаем маршрутизацию к следующим агентам
                await self._process_routing_chain(next_agents, agent_message)
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при обработке агентом {agent_name}: {e}")
            return f"❌ Ошибка обработки агентом {agent_name}: {e}"
    
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
        
        # Не продолжаем если слишком длинная цепочка
        recent_agent_messages = [
            msg for msg in self.conversation_history[-5:]
            if msg.sender == agent_name
        ]
        
        return len(recent_agent_messages) < 3
    
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
            "created_at": datetime.now(),
            "result": None
        }
        
        self.active_tasks[task_id] = task
        
        # Отправляем задачу агенту
        task_message = Message(
            sender="system",
            recipient=assigned_agent,
            content=f"Новая задача: {task_description}",
            timestamp=datetime.now(),
            message_type="task",
            metadata={"task_id": task_id}
        )
        
        await self._route_message_to_agent(assigned_agent, task_message)
        
        return task_id
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        return {
            "agents_count": len(self.agents),
            "routing_rules": len(self.routing),
            "conversation_length": len(self.conversation_history),
            "active_tasks": len(self.active_tasks),
            "system_health": "healthy",
            "uptime": datetime.now().isoformat()
        }


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
        
        def generate_reply(self, messages=None, sender=None):
            return f"[{self.name}] Обработано {len(messages)} сообщений"
    
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