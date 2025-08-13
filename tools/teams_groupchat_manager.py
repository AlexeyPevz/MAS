"""
Teams-Enhanced GroupChat Manager
Расширение SmartGroupChatManager с использованием Teams API из AutoGen v0.4
"""
import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timezone
import json

from tools.smart_groupchat import SmartGroupChatManager, Message

# AutoGen v0.4 Teams API
try:
    from autogen_agentchat.teams import (
        Team,
        RoundRobinGroupChat,
        SelectorGroupChat,
        Swarm
    )
    from autogen_agentchat.conditions import (
        TextMentionTermination,
        MaxMessageTermination,
        HandoffTermination
    )
    from autogen_agentchat.agents import AssistantAgent
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    TEAMS_API_AVAILABLE = True
except ImportError:
    TEAMS_API_AVAILABLE = False
    Team = None

logger = logging.getLogger(__name__)


@dataclass
class TeamTask:
    """Задача для команды"""
    id: str
    type: str  # research, development, analysis, creative
    query: str
    priority: int = 1
    context: Dict[str, Any] = None
    constraints: List[str] = None
    expected_output: str = None


class TeamsGroupChatManager(SmartGroupChatManager):
    """GroupChat Manager с поддержкой Teams API"""
    
    def __init__(self, agents: Dict[str, Any] = None, routing: Dict[str, List[str]] = None):
        super().__init__(agents, routing)
        self.teams: Dict[str, Team] = {}
        self.model_client = None
        self._setup_teams()
        
    def _setup_teams(self):
        """Инициализация команд"""
        if not TEAMS_API_AVAILABLE:
            logger.warning("Teams API not available, using basic mode")
            return
            
        # Создаем model client
        self.model_client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Создаем специализированные команды
        self._create_research_team()
        self._create_development_team()
        self._create_analysis_team()
        self._create_creative_team()
        
    def _create_research_team(self):
        """Команда исследователей"""
        if not self.agents:
            return
            
        # Выбираем агентов для исследовательской команды
        research_agents = []
        
        if "researcher" in self.agents:
            research_agents.append(self.agents["researcher"])
        if "fact_checker" in self.agents:
            research_agents.append(self.agents["fact_checker"])
        if "multitool" in self.agents:
            research_agents.append(self.agents["multitool"])
            
        if len(research_agents) >= 2:
            # Условие завершения - найдено решение или максимум итераций
            termination = TextMentionTermination("ИССЛЕДОВАНИЕ ЗАВЕРШЕНО") | MaxMessageTermination(10)
            
            # Создаем команду с селектором для умного выбора агентов
            self.teams["research"] = SelectorGroupChat(
                participants=research_agents,
                model_client=self.model_client,
                termination_condition=termination,
                selector_prompt="""Выбери следующего агента на основе текущего состояния исследования:
                - Если нужно найти информацию: researcher
                - Если нужно проверить факты: fact_checker
                - Если нужно использовать внешние инструменты: multitool
                Учитывай, кто уже участвовал и что было сделано."""
            )
            
    def _create_development_team(self):
        """Команда разработки"""
        if not self.agents:
            return
            
        dev_agents = []
        
        if "agent_builder" in self.agents:
            dev_agents.append(self.agents["agent_builder"])
        if "workflow_builder" in self.agents:
            dev_agents.append(self.agents["workflow_builder"])
        if "webapp_builder" in self.agents:
            dev_agents.append(self.agents["webapp_builder"])
            
        if len(dev_agents) >= 2:
            # Round-robin для последовательной разработки
            self.teams["development"] = RoundRobinGroupChat(
                participants=dev_agents,
                termination_condition=MaxMessageTermination(8)
            )
            
    def _create_analysis_team(self):
        """Команда аналитиков"""
        if not self.agents:
            return
            
        analysis_agents = []
        
        if "meta" in self.agents:
            analysis_agents.append(self.agents["meta"])
        if "model_selector" in self.agents:
            analysis_agents.append(self.agents["model_selector"])
        if "prompt_builder" in self.agents:
            analysis_agents.append(self.agents["prompt_builder"])
            
        if len(analysis_agents) >= 2:
            self.teams["analysis"] = RoundRobinGroupChat(
                participants=analysis_agents,
                termination_condition=MaxMessageTermination(6)
            )
            
    def _create_creative_team(self):
        """Команда для творческих задач"""
        if not self.agents:
            return
            
        creative_agents = []
        
        if "webapp_builder" in self.agents:
            creative_agents.append(self.agents["webapp_builder"])
        if "prompt_builder" in self.agents:
            creative_agents.append(self.agents["prompt_builder"])
        if "communicator" in self.agents:
            creative_agents.append(self.agents["communicator"])
            
        if len(creative_agents) >= 2:
            # Используем Swarm для творческих задач (если доступен)
            try:
                self.teams["creative"] = Swarm(
                    participants=creative_agents,
                    termination_condition=MaxMessageTermination(10)
                )
            except:
                # Fallback на RoundRobin
                self.teams["creative"] = RoundRobinGroupChat(
                    participants=creative_agents,
                    termination_condition=MaxMessageTermination(10)
                )
    
    async def process_with_team(self, task: TeamTask) -> Dict[str, Any]:
        """Обработка задачи с использованием подходящей команды"""
        if not TEAMS_API_AVAILABLE or task.type not in self.teams:
            # Fallback на обычную обработку
            return await self.process_message(task.query, task.id)
            
        team = self.teams[task.type]
        
        logger.info(f"🏢 Обработка задачи типа '{task.type}' командой")
        
        try:
            # Формируем контекст для команды
            context_prompt = self._build_team_context(task)
            
            # Запускаем команду
            result = await team.run(task=context_prompt)
            
            # Обрабатываем результат
            team_response = {
                "task_id": task.id,
                "task_type": task.type,
                "team_used": task.type,
                "messages_count": len(result.messages),
                "result": result.messages[-1].content if result.messages else "No result",
                "participants": [msg.source for msg in result.messages],
                "success": True
            }
            
            # Сохраняем в историю
            self._save_team_result(task, team_response)
            
            return team_response
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки командой: {e}")
            return {
                "task_id": task.id,
                "task_type": task.type,
                "error": str(e),
                "success": False
            }
    
    def _build_team_context(self, task: TeamTask) -> str:
        """Построение контекста для команды"""
        context_parts = [f"Задача: {task.query}"]
        
        if task.context:
            context_parts.append(f"\nКонтекст: {json.dumps(task.context, ensure_ascii=False)}")
            
        if task.constraints:
            context_parts.append(f"\nОграничения: {', '.join(task.constraints)}")
            
        if task.expected_output:
            context_parts.append(f"\nОжидаемый результат: {task.expected_output}")
            
        return "\n".join(context_parts)
    
    def _save_team_result(self, task: TeamTask, result: Dict[str, Any]):
        """Сохранение результата работы команды"""
        message = Message(
            sender=f"team_{task.type}",
            recipient="system",
            content=result["result"],
            timestamp=datetime.now(timezone.utc),
            message_type="team_result",
            metadata={
                "task_id": task.id,
                "task_type": task.type,
                "participants": result.get("participants", []),
                "messages_count": result.get("messages_count", 0)
            }
        )
        
        self.conversation_history.append(message)
        
    async def analyze_task_and_route(self, query: str, user_id: str) -> TeamTask:
        """Анализ задачи и определение подходящей команды"""
        # Простой анализ на основе ключевых слов
        # В будущем можно использовать ML классификатор
        
        task_type = "general"
        priority = 1
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["исследуй", "найди", "узнай", "проверь факт"]):
            task_type = "research"
            priority = 2
        elif any(word in query_lower for word in ["создай", "разработай", "построй", "сгенерируй"]):
            task_type = "development"
            priority = 2
        elif any(word in query_lower for word in ["проанализируй", "оцени", "сравни"]):
            task_type = "analysis"
            priority = 2
        elif any(word in query_lower for word in ["придумай", "напиши", "сочини"]):
            task_type = "creative"
            priority = 1
            
        return TeamTask(
            id=f"{user_id}_{datetime.now().timestamp()}",
            type=task_type,
            query=query,
            priority=priority
        )
    
    async def process_message(self, message: str, sender_id: str = "user") -> str:
        """Переопределенный метод обработки с поддержкой Teams"""
        
        # Анализируем задачу
        task = await self.analyze_task_and_route(message, sender_id)
        
        # Если есть подходящая команда - используем её
        if TEAMS_API_AVAILABLE and task.type in self.teams:
            logger.info(f"🎯 Маршрутизация на команду '{task.type}'")
            
            result = await self.process_with_team(task)
            
            if result.get("success"):
                return result["result"]
            else:
                logger.warning(f"⚠️ Команда не справилась, использую обычную обработку")
                
        # Fallback на обычную обработку
        return await super().process_message(message, sender_id)
    
    def get_teams_status(self) -> Dict[str, Any]:
        """Получение статуса команд"""
        status = {
            "teams_available": TEAMS_API_AVAILABLE,
            "active_teams": list(self.teams.keys()),
            "teams_details": {}
        }
        
        for team_name, team in self.teams.items():
            status["teams_details"][team_name] = {
                "type": type(team).__name__,
                "participants": [p.name for p in team.participants] if hasattr(team, 'participants') else [],
                "ready": True
            }
            
        return status
    
    async def create_dynamic_team(
        self,
        agents: List[Any],
        task: str,
        team_type: str = "selector"
    ) -> Optional[Team]:
        """Создание динамической команды для конкретной задачи"""
        if not TEAMS_API_AVAILABLE or len(agents) < 2:
            return None
            
        try:
            if team_type == "selector":
                team = SelectorGroupChat(
                    participants=agents,
                    model_client=self.model_client,
                    termination_condition=MaxMessageTermination(10),
                    selector_prompt=f"Выбери агента для задачи: {task}"
                )
            elif team_type == "roundrobin":
                team = RoundRobinGroupChat(
                    participants=agents,
                    termination_condition=MaxMessageTermination(len(agents) * 2)
                )
            elif team_type == "swarm":
                team = Swarm(
                    participants=agents,
                    termination_condition=MaxMessageTermination(15)
                )
            else:
                return None
                
            return team
            
        except Exception as e:
            logger.error(f"Ошибка создания динамической команды: {e}")
            return None


# Пример использования
async def example_usage():
    """Пример использования Teams-enhanced GroupChat Manager"""
    
    # Создаем менеджер (агенты будут загружены из конфигурации)
    manager = TeamsGroupChatManager()
    await manager.initialize()
    
    # Пример задач разных типов
    tasks = [
        "Исследуй последние тренды в области AI агентов",
        "Создай простое веб-приложение для управления задачами",
        "Проанализируй эффективность различных LLM моделей",
        "Напиши креативную историю про робота-помощника"
    ]
    
    for task_query in tasks:
        print(f"\n📋 Задача: {task_query}")
        
        # Обрабатываем через команды
        response = await manager.process_message(task_query, "example_user")
        
        print(f"✅ Ответ: {response[:200]}...")
        
    # Статус команд
    status = manager.get_teams_status()
    print(f"\n📊 Статус команд: {json.dumps(status, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    import os
    
    # Проверяем наличие ключа
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY не установлен")
    else:
        asyncio.run(example_usage())