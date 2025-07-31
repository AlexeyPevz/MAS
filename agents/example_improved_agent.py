"""
Example of improved agent implementation
"""
from typing import List, Dict, Any, Optional
import json
from dataclasses import dataclass
from datetime import datetime
from agents.base import BaseAgent


@dataclass
class Task:
    id: str
    title: str
    description: str
    priority: int  # 1-5
    status: str  # pending, in_progress, completed, blocked
    assigned_to: Optional[str] = None
    dependencies: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.dependencies is None:
            self.dependencies = []


class ImprovedCoordinationAgent(BaseAgent):
    """Улучшенный агент координации с реальной логикой управления задачами"""
    
    def __init__(self, tier="cheap", model=None):
        super().__init__("coordination", model, tier)
        self.tasks: Dict[str, Task] = {}
        self.agent_workload: Dict[str, int] = {}
        
    def generate_reply(self, messages, sender=None, **kwargs):
        """Обработка сообщений с реальной логикой"""
        if not messages:
            return "Нет сообщений для обработки"
            
        last_message = messages[-1]["content"] if isinstance(messages[-1], dict) else str(messages[-1])
        
        # Анализируем намерение
        intent = self._analyze_intent(last_message)
        
        if intent == "create_task":
            return self._handle_create_task(last_message)
        elif intent == "status_update":
            return self._handle_status_update()
        elif intent == "assign_task":
            return self._handle_task_assignment(last_message)
        elif intent == "get_bottlenecks":
            return self._analyze_bottlenecks()
        else:
            return self._handle_general_coordination(last_message)
    
    def _analyze_intent(self, message: str) -> str:
        """Определение намерения из сообщения"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["создай", "новая задача", "create task", "добавь задачу"]):
            return "create_task"
        elif any(word in message_lower for word in ["статус", "status", "прогресс", "progress"]):
            return "status_update"
        elif any(word in message_lower for word in ["назначь", "assign", "передай"]):
            return "assign_task"
        elif any(word in message_lower for word in ["bottleneck", "проблема", "блокировка", "застрял"]):
            return "get_bottlenecks"
        else:
            return "general"
    
    def _handle_create_task(self, message: str) -> str:
        """Создание новой задачи"""
        # Извлекаем информацию о задаче из сообщения
        task_info = self._extract_task_info(message)
        
        task = Task(
            id=f"TASK-{len(self.tasks) + 1:04d}",
            title=task_info.get("title", "Новая задача"),
            description=task_info.get("description", message),
            priority=task_info.get("priority", 3),
            status="pending"
        )
        
        self.tasks[task.id] = task
        
        return f"""✅ Создана новая задача:
**ID**: {task.id}
**Название**: {task.title}
**Приоритет**: {'🔴' * task.priority}{'⚪' * (5 - task.priority)}
**Статус**: {task.status}

Задача добавлена в очередь. Используйте ID {task.id} для дальнейших операций."""
    
    def _handle_status_update(self) -> str:
        """Предоставление обновления статуса"""
        if not self.tasks:
            return "📊 Нет активных задач в системе"
        
        stats = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "blocked": 0
        }
        
        for task in self.tasks.values():
            stats[task.status] += 1
        
        # Формируем красивый отчет
        report = "📊 **Статус системы координации**\n\n"
        report += f"**Всего задач**: {len(self.tasks)}\n\n"
        report += "**По статусам**:\n"
        report += f"⏳ Ожидают: {stats['pending']}\n"
        report += f"🔄 В работе: {stats['in_progress']}\n"
        report += f"✅ Завершены: {stats['completed']}\n"
        report += f"🚫 Заблокированы: {stats['blocked']}\n\n"
        
        # Добавляем топ приоритетных задач
        priority_tasks = sorted(
            [t for t in self.tasks.values() if t.status in ['pending', 'in_progress']], 
            key=lambda x: x.priority, 
            reverse=True
        )[:3]
        
        if priority_tasks:
            report += "**🔥 Приоритетные задачи**:\n"
            for task in priority_tasks:
                report += f"- [{task.id}] {task.title} ({'🔴' * task.priority})\n"
        
        return report
    
    def _handle_task_assignment(self, message: str) -> str:
        """Назначение задачи агенту"""
        # Простая логика извлечения task_id и agent_name
        parts = message.lower().split()
        task_id = None
        agent_name = None
        
        for i, part in enumerate(parts):
            if part.startswith("task-") and i + 2 < len(parts):
                task_id = part.upper()
                # Ищем имя агента после task_id
                for j in range(i + 1, len(parts)):
                    if parts[j] in ["meta", "researcher", "builder", "checker"]:
                        agent_name = parts[j]
                        break
        
        if not task_id or task_id not in self.tasks:
            return "❌ Не найдена задача для назначения. Укажите корректный ID задачи."
        
        if not agent_name:
            # Автоматический выбор наименее загруженного агента
            agent_name = self._find_least_busy_agent()
        
        task = self.tasks[task_id]
        task.assigned_to = agent_name
        task.status = "in_progress"
        task.updated_at = datetime.now()
        
        # Обновляем загрузку агента
        if agent_name not in self.agent_workload:
            self.agent_workload[agent_name] = 0
        self.agent_workload[agent_name] += 1
        
        return f"""✅ Задача назначена:
**Задача**: {task.id} - {task.title}
**Исполнитель**: {agent_name}
**Статус**: Передана в работу

Агент {agent_name} уведомлен и приступил к выполнению."""
    
    def _analyze_bottlenecks(self) -> str:
        """Анализ узких мест в системе"""
        bottlenecks = []
        
        # Проверяем заблокированные задачи
        blocked_tasks = [t for t in self.tasks.values() if t.status == "blocked"]
        if blocked_tasks:
            bottlenecks.append(f"🚫 Заблокировано задач: {len(blocked_tasks)}")
        
        # Проверяем перегруженных агентов
        overloaded_agents = [(agent, load) for agent, load in self.agent_workload.items() if load > 3]
        if overloaded_agents:
            for agent, load in overloaded_agents:
                bottlenecks.append(f"⚠️ Агент {agent} перегружен: {load} задач")
        
        # Проверяем старые задачи
        old_tasks = []
        for task in self.tasks.values():
            if task.status == "in_progress":
                age = (datetime.now() - task.created_at).days
                if age > 3:
                    old_tasks.append(task)
        
        if old_tasks:
            bottlenecks.append(f"⏰ Задач в работе более 3 дней: {len(old_tasks)}")
        
        if not bottlenecks:
            return "✅ Узких мест не обнаружено. Система работает оптимально."
        
        report = "⚠️ **Обнаружены узкие места**:\n\n"
        for bottleneck in bottlenecks:
            report += f"{bottleneck}\n"
        
        report += "\n**Рекомендации**:\n"
        report += "- Разблокируйте задачи или переназначьте их\n"
        report += "- Распределите нагрузку между агентами\n"
        report += "- Проверьте старые задачи на актуальность"
        
        return report
    
    def _extract_task_info(self, message: str) -> Dict[str, Any]:
        """Извлечение информации о задаче из сообщения"""
        # Простой парсер, в реальности здесь был бы NLP
        info = {
            "title": "Новая задача",
            "description": message,
            "priority": 3
        }
        
        # Ищем приоритет
        if "срочно" in message.lower() or "urgent" in message.lower():
            info["priority"] = 5
        elif "важно" in message.lower() or "important" in message.lower():
            info["priority"] = 4
        
        # Пытаемся извлечь название
        if ":" in message:
            parts = message.split(":", 1)
            potential_title = parts[0].strip()
            if len(potential_title) < 100:  # Разумная длина для заголовка
                info["title"] = potential_title
                info["description"] = parts[1].strip() if len(parts) > 1 else message
        
        return info
    
    def _find_least_busy_agent(self) -> str:
        """Поиск наименее загруженного агента"""
        available_agents = ["researcher", "builder", "checker", "analyzer"]
        
        least_busy = None
        min_load = float('inf')
        
        for agent in available_agents:
            load = self.agent_workload.get(agent, 0)
            if load < min_load:
                min_load = load
                least_busy = agent
        
        return least_busy or "researcher"
    
    def _handle_general_coordination(self, message: str) -> str:
        """Общая координационная логика"""
        return f"""🤖 Координационный агент обработал ваш запрос.

Я могу помочь с:
- Созданием и управлением задачами
- Назначением задач агентам
- Отслеживанием прогресса
- Анализом узких мест
- Оптимизацией рабочих процессов

Что именно вас интересует?"""