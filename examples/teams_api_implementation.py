"""
Teams API для сложных многоагентных сценариев в Root-MAS
"""
from typing import List, Dict, Any, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import (
    RoundRobinGroupChat,
    SelectorGroupChat, 
    Team
)
from autogen_agentchat.conditions import (
    TextMentionTermination,
    MaxMessageTermination,
    HandoffTermination
)
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient

class RootMASTeamsOrchestrator:
    """Оркестратор команд для сложных сценариев"""
    
    def __init__(self):
        self.model_client = self._create_model_client()
        self.teams = {}
        self._setup_teams()
    
    def _create_model_client(self):
        return OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key="your-key",
            base_url="https://openrouter.ai/api/v1"
        )
    
    def _setup_teams(self):
        """Настройка специализированных команд"""
        
        # 1. Команда исследователей
        self.teams["research"] = self._create_research_team()
        
        # 2. Команда разработки
        self.teams["development"] = self._create_development_team()
        
        # 3. Команда контроля качества
        self.teams["quality"] = self._create_quality_team()
        
        # 4. Мета-команда координации
        self.teams["meta"] = self._create_meta_team()
    
    def _create_research_team(self) -> Team:
        """Команда для исследовательских задач"""
        
        # Специализированные агенты
        researcher = AssistantAgent(
            name="researcher",
            description="Исследует информацию и находит решения",
            system_message="""Ты исследователь. Твоя задача - глубоко изучать вопросы,
            находить информацию и предлагать решения. Когда найдешь решение, скажи 'РЕШЕНИЕ НАЙДЕНО'.""",
            model_client=self.model_client
        )
        
        fact_checker = AssistantAgent(
            name="fact_checker",
            description="Проверяет факты и валидирует информацию",
            system_message="""Ты проверяешь факты. Анализируй предложенную информацию,
            указывай на неточности. Если всё корректно, скажи 'ФАКТЫ ПОДТВЕРЖДЕНЫ'.""",
            model_client=self.model_client
        )
        
        analyst = AssistantAgent(
            name="analyst",
            description="Анализирует данные и делает выводы",
            system_message="""Ты аналитик. Синтезируй информацию от других агентов
            и делай структурированные выводы.""",
            model_client=self.model_client
        )
        
        # Условие завершения - когда решение найдено и факты проверены
        termination = (
            TextMentionTermination("РЕШЕНИЕ НАЙДЕНО") & 
            TextMentionTermination("ФАКТЫ ПОДТВЕРЖДЕНЫ")
        ) | MaxMessageTermination(10)
        
        # Создаем команду с SelectorGroupChat для умного выбора следующего агента
        return SelectorGroupChat(
            participants=[researcher, fact_checker, analyst],
            model_client=self.model_client,
            termination_condition=termination,
            max_turns=10,
            selector_prompt="""Выбери следующего агента на основе контекста:
            - Если нужно найти информацию: researcher
            - Если нужно проверить факты: fact_checker  
            - Если нужно сделать выводы: analyst"""
        )
    
    def _create_development_team(self) -> Team:
        """Команда разработки с последовательным workflow"""
        
        architect = AssistantAgent(
            name="architect",
            description="Проектирует архитектуру решения",
            system_message="Ты архитектор. Проектируй структуру и компоненты системы.",
            model_client=self.model_client
        )
        
        developer = AssistantAgent(
            name="developer",
            description="Реализует код",
            system_message="Ты разработчик. Пиши чистый, эффективный код.",
            model_client=self.model_client
        )
        
        reviewer = AssistantAgent(
            name="reviewer",
            description="Ревьюит код и архитектуру",
            system_message="Ты ревьюер. Проверяй качество кода и архитектуры.",
            model_client=self.model_client
        )
        
        # Round-robin для последовательной работы
        return RoundRobinGroupChat(
            participants=[architect, developer, reviewer],
            termination_condition=MaxMessageTermination(6),
            max_turns=6
        )
    
    def _create_quality_team(self) -> Team:
        """Команда контроля качества"""
        
        tester = AssistantAgent(
            name="tester",
            description="Тестирует решения",
            system_message="Ты тестировщик. Проверяй edge cases и находи проблемы.",
            model_client=self.model_client
        )
        
        performance_analyst = AssistantAgent(
            name="performance_analyst",
            description="Анализирует производительность",
            system_message="Ты специалист по производительности. Оценивай эффективность решений.",
            model_client=self.model_client
        )
        
        return RoundRobinGroupChat(
            participants=[tester, performance_analyst],
            max_turns=4
        )
    
    def _create_meta_team(self) -> Team:
        """Мета-команда для координации других команд"""
        
        meta_coordinator = AssistantAgent(
            name="meta_coordinator",
            description="Координирует работу всех команд",
            system_message="""Ты мета-координатор Root-MAS. Твоя задача:
            1. Анализировать входящие задачи
            2. Распределять их между командами
            3. Координировать взаимодействие
            4. Синтезировать финальный результат
            
            Используй HANDOFF для передачи задач другим командам.""",
            model_client=self.model_client,
            handoffs=["research_team", "development_team", "quality_team"]
        )
        
        return RoundRobinGroupChat(
            participants=[meta_coordinator],
            max_turns=1
        )
    
    async def process_complex_task(self, task: str) -> Dict[str, Any]:
        """Обработка сложной задачи через систему команд"""
        
        results = {
            "task": task,
            "teams_involved": [],
            "stages": []
        }
        
        # 1. Начинаем с мета-команды
        meta_result = await self.teams["meta"].run(task=task)
        results["stages"].append({
            "team": "meta",
            "decision": meta_result.messages[-1].content
        })
        
        # 2. Определяем, какие команды нужны (упрощенная логика)
        if "исследовать" in task.lower() or "найти" in task.lower():
            research_result = await self.teams["research"].run(
                task=f"Исследовательская задача: {task}"
            )
            results["teams_involved"].append("research")
            results["stages"].append({
                "team": "research",
                "messages": len(research_result.messages),
                "conclusion": research_result.messages[-1].content
            })
        
        if "разработать" in task.lower() or "создать" in task.lower():
            dev_result = await self.teams["development"].run(
                task=f"Задача разработки: {task}"
            )
            results["teams_involved"].append("development")
            results["stages"].append({
                "team": "development",
                "messages": len(dev_result.messages),
                "result": dev_result.messages[-1].content
            })
            
            # Автоматически запускаем QA после разработки
            qa_result = await self.teams["quality"].run(
                task=f"Проверить качество: {dev_result.messages[-1].content[:200]}..."
            )
            results["teams_involved"].append("quality")
            results["stages"].append({
                "team": "quality",
                "verdict": qa_result.messages[-1].content
            })
        
        return results

# Пример параллельной работы команд
class ParallelTeamsOrchestrator(RootMASTeamsOrchestrator):
    """Оркестратор с параллельной работой команд"""
    
    async def process_parallel_tasks(self, tasks: List[str]) -> List[Dict[str, Any]]:
        """Обработка нескольких задач параллельно разными командами"""
        import asyncio
        
        # Создаем задачи для параллельного выполнения
        async_tasks = []
        
        for task in tasks:
            # Определяем подходящую команду для задачи
            if "исследовать" in task.lower():
                team = self.teams["research"]
            elif "разработать" in task.lower():
                team = self.teams["development"]
            else:
                team = self.teams["meta"]
            
            # Создаем асинхронную задачу
            async_task = asyncio.create_task(
                self._process_with_team(team, task)
            )
            async_tasks.append(async_task)
        
        # Запускаем все задачи параллельно
        results = await asyncio.gather(*async_tasks)
        
        return results
    
    async def _process_with_team(self, team: Team, task: str) -> Dict[str, Any]:
        """Обработка задачи конкретной командой"""
        result = await team.run(task=task)
        
        return {
            "task": task,
            "team": team.participants[0].name if team.participants else "unknown",
            "messages_count": len(result.messages),
            "final_response": result.messages[-1].content if result.messages else ""
        }

# Пример адаптивной команды с динамическим составом
class AdaptiveTeam(Team):
    """Команда, которая адаптирует свой состав под задачу"""
    
    def __init__(self, orchestrator: RootMASTeamsOrchestrator):
        self.orchestrator = orchestrator
        self.agent_pool = self._create_agent_pool()
        
    def _create_agent_pool(self) -> Dict[str, AssistantAgent]:
        """Создаем пул всех доступных агентов"""
        return {
            "python_expert": AssistantAgent(
                name="python_expert",
                description="Эксперт по Python",
                system_message="Ты эксперт по Python и его экосистеме.",
                model_client=self.orchestrator.model_client
            ),
            "ml_expert": AssistantAgent(
                name="ml_expert", 
                description="Эксперт по машинному обучению",
                system_message="Ты эксперт по ML и data science.",
                model_client=self.orchestrator.model_client
            ),
            "devops_expert": AssistantAgent(
                name="devops_expert",
                description="Эксперт по DevOps",
                system_message="Ты эксперт по DevOps, Docker, K8s.",
                model_client=self.orchestrator.model_client
            ),
            # ... другие эксперты
        }
    
    async def assemble_team_for_task(self, task: str) -> Team:
        """Собираем команду под конкретную задачу"""
        
        # Анализируем задачу и выбираем нужных агентов
        selected_agents = []
        
        if "python" in task.lower() or "код" in task.lower():
            selected_agents.append(self.agent_pool["python_expert"])
        
        if "ml" in task.lower() or "машинное обучение" in task.lower():
            selected_agents.append(self.agent_pool["ml_expert"])
            
        if "docker" in task.lower() or "развертывание" in task.lower():
            selected_agents.append(self.agent_pool["devops_expert"])
        
        # Если не выбрали специфичных, берем общих
        if not selected_agents:
            selected_agents = list(self.agent_pool.values())[:3]
        
        # Создаем динамическую команду
        return SelectorGroupChat(
            participants=selected_agents,
            model_client=self.orchestrator.model_client,
            termination_condition=MaxMessageTermination(6)
        )