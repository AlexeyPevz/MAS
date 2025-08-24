"""
Hybrid Approach: SGR + Function Calling
Демонстрация гибридного подхода, сочетающего структурированное рассуждение с агентским поведением
"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
import json
from datetime import datetime

# Импортируем компоненты из предыдущих примеров
from sgr_example import SGRReasoning, SGRResponse, QueryAnalysis
from function_calling_example import ToolManager, Tool, WebSearchTool, DatabaseTool, EmailTool

# Схемы для гибридного подхода

class ActionType(str, Enum):
    DIRECT_RESPONSE = "direct_response"
    USE_TOOLS = "use_tools"
    COMPLEX_WORKFLOW = "complex_workflow"

class ToolPlan(BaseModel):
    """План использования инструментов"""
    tool_name: str
    parameters: Dict[str, Any]
    purpose: str = Field(description="Цель использования инструмента")
    expected_output: str = Field(description="Ожидаемый результат")

class WorkflowStep(BaseModel):
    """Шаг в workflow"""
    step_number: int
    action_type: ActionType
    description: str
    tool_plans: List[ToolPlan] = Field(default_factory=list)
    dependencies: List[int] = Field(default_factory=list, description="Номера шагов, от которых зависит этот шаг")

class HybridPlanningReasoning(BaseModel):
    """SGR для планирования гибридного подхода"""
    query_analysis: QueryAnalysis
    action_classification: str = Field(description="Классификация типа действия")
    complexity_assessment: str = Field(description="Оценка сложности задачи")
    workflow_steps: List[WorkflowStep] = Field(description="Запланированные шаги workflow")
    reasoning_trace: List[str] = Field(description="Трассировка рассуждений планирования")

class ToolExecutionResult(BaseModel):
    """Результат выполнения инструмента"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    execution_time: Optional[str] = None

class ResultProcessingReasoning(BaseModel):
    """SGR для обработки результатов"""
    tool_results_analysis: List[str] = Field(description="Анализ результатов каждого инструмента")
    data_integration: str = Field(description="Способ интеграции данных из разных источников")
    quality_assessment: str = Field(description="Оценка качества полученных данных")
    completeness_check: str = Field(description="Проверка полноты ответа")
    reasoning_trace: List[str] = Field(description="Трассировка обработки результатов")

class HybridResponse(BaseModel):
    """Финальный ответ гибридного подхода"""
    planning_reasoning: HybridPlanningReasoning
    tool_executions: List[ToolExecutionResult]
    processing_reasoning: ResultProcessingReasoning
    final_response: str
    confidence_score: float = Field(ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Гибридный агент
class HybridAgent:
    def __init__(self, tool_manager: ToolManager):
        self.tool_manager = tool_manager
        
    def create_planning_prompt(self, user_query: str) -> str:
        """Создает промпт для SGR планирования"""
        tools_schema = self.tool_manager.get_tools_schema()
        
        prompt = f"""
Ты эксперт по планированию задач с доступом к инструментам. Проанализируй запрос пользователя и составь структурированный план.

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {user_query}

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
{json.dumps(tools_schema, ensure_ascii=False, indent=2)}

Проведи анализ по следующей схеме:

1. АНАЛИЗ ЗАПРОСА (query_analysis):
   - Определи тип запроса и ключевые сущности
   - Выяви намерение пользователя

2. КЛАССИФИКАЦИЯ ДЕЙСТВИЯ (action_classification):
   - direct_response: можно ответить без инструментов
   - use_tools: нужны инструменты для получения данных
   - complex_workflow: требуется многошаговый процесс

3. ОЦЕНКА СЛОЖНОСТИ (complexity_assessment):
   - Простая, средняя или высокая сложность
   - Обоснование оценки

4. ПЛАНИРОВАНИЕ WORKFLOW (workflow_steps):
   - Разбей на логические шаги
   - Для каждого шага определи нужные инструменты
   - Укажи зависимости между шагами

Верни результат в формате JSON согласно схеме HybridPlanningReasoning.
"""
        return prompt
    
    def create_processing_prompt(self, user_query: str, tool_results: List[ToolExecutionResult]) -> str:
        """Создает промпт для SGR обработки результатов"""
        
        prompt = f"""
Ты эксперт по обработке данных. Проанализируй результаты выполнения инструментов и сформируй финальный ответ.

ИСХОДНЫЙ ЗАПРОС: {user_query}

РЕЗУЛЬТАТЫ ИНСТРУМЕНТОВ:
{json.dumps([result.model_dump() for result in tool_results], ensure_ascii=False, indent=2)}

Проведи анализ по следующей схеме:

1. АНАЛИЗ РЕЗУЛЬТАТОВ (tool_results_analysis):
   - Проанализируй результат каждого инструмента
   - Оцени качество и полноту данных

2. ИНТЕГРАЦИЯ ДАННЫХ (data_integration):
   - Опиши, как объединить данные из разных источников
   - Выяви связи и закономерности

3. ОЦЕНКА КАЧЕСТВА (quality_assessment):
   - Насколько хорошо данные отвечают на запрос
   - Есть ли противоречия или пробелы

4. ПРОВЕРКА ПОЛНОТЫ (completeness_check):
   - Достаточно ли данных для полного ответа
   - Что еще может понадобиться

5. ФИНАЛЬНЫЙ ОТВЕТ:
   - Сформулируй четкий и полный ответ
   - Укажи источники информации

Верни результат в формате JSON согласно схеме ResultProcessingReasoning.
"""
        return prompt
    
    def execute_workflow(self, workflow_steps: List[WorkflowStep]) -> List[ToolExecutionResult]:
        """Выполняет запланированные шаги workflow"""
        results = []
        step_results = {}  # Для хранения результатов шагов
        
        for step in sorted(workflow_steps, key=lambda x: x.step_number):
            print(f"Выполняю шаг {step.step_number}: {step.description}")
            
            # Проверяем зависимости
            for dependency in step.dependencies:
                if dependency not in step_results:
                    print(f"Внимание: зависимость {dependency} не выполнена")
            
            if step.action_type == ActionType.USE_TOOLS:
                # Выполняем инструменты для этого шага
                for tool_plan in step.tool_plans:
                    start_time = datetime.now()
                    
                    result = self.tool_manager.execute_tool(
                        tool_plan.tool_name,
                        **tool_plan.parameters
                    )
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    tool_result = ToolExecutionResult(
                        tool_name=tool_plan.tool_name,
                        parameters=tool_plan.parameters,
                        result=result,
                        success=result.get("success", True),
                        execution_time=f"{execution_time:.2f}s"
                    )
                    
                    results.append(tool_result)
                    print(f"  - Выполнен {tool_plan.tool_name}: {tool_plan.purpose}")
            
            step_results[step.step_number] = True
        
        return results
    
    def process_query(self, user_query: str) -> HybridResponse:
        """Обрабатывает запрос в гибридном режиме"""
        
        # Этап 1: SGR планирование
        print("=== ЭТАП 1: ПЛАНИРОВАНИЕ (SGR) ===")
        planning_reasoning = self._simulate_planning_reasoning(user_query)
        
        # Этап 2: Выполнение инструментов (Function Calling)
        print("\n=== ЭТАП 2: ВЫПОЛНЕНИЕ ИНСТРУМЕНТОВ ===")
        tool_executions = self.execute_workflow(planning_reasoning.workflow_steps)
        
        # Этап 3: SGR обработка результатов
        print("\n=== ЭТАП 3: ОБРАБОТКА РЕЗУЛЬТАТОВ (SGR) ===")
        processing_reasoning = self._simulate_processing_reasoning(user_query, tool_executions)
        
        # Формируем финальный ответ
        final_response = self._generate_final_response(user_query, tool_executions, processing_reasoning)
        
        return HybridResponse(
            planning_reasoning=planning_reasoning,
            tool_executions=tool_executions,
            processing_reasoning=processing_reasoning,
            final_response=final_response,
            confidence_score=0.9,
            metadata={
                "approach": "hybrid_sgr_tools",
                "steps_executed": len(planning_reasoning.workflow_steps),
                "tools_used": len(tool_executions),
                "processing_time": "simulated"
            }
        )
    
    def _simulate_planning_reasoning(self, user_query: str) -> HybridPlanningReasoning:
        """Симулирует SGR планирование"""
        
        # Определяем тип запроса
        if "проект" in user_query.lower() and "отправь" in user_query.lower():
            # Сложный workflow: получить данные + отправить email
            return HybridPlanningReasoning(
                query_analysis=QueryAnalysis(
                    user_query=user_query,
                    query_type="комплексное_действие",
                    key_entities=["проекты", "email", "отчет"],
                    intent="получить_данные_и_отправить_отчет"
                ),
                action_classification="complex_workflow",
                complexity_assessment="высокая - требует получения данных и отправки email",
                workflow_steps=[
                    WorkflowStep(
                        step_number=1,
                        action_type=ActionType.USE_TOOLS,
                        description="Получить данные о проектах из базы",
                        tool_plans=[
                            ToolPlan(
                                tool_name="database_query",
                                parameters={"query": "SELECT * FROM projects"},
                                purpose="получить_список_проектов",
                                expected_output="список_всех_проектов"
                            )
                        ]
                    ),
                    WorkflowStep(
                        step_number=2,
                        action_type=ActionType.USE_TOOLS,
                        description="Отправить отчет по email",
                        tool_plans=[
                            ToolPlan(
                                tool_name="send_email",
                                parameters={
                                    "to": "manager@company.com",
                                    "subject": "Отчет по проектам",
                                    "body": "Отчет будет сформирован на основе данных"
                                },
                                purpose="отправить_отчет",
                                expected_output="подтверждение_отправки"
                            )
                        ],
                        dependencies=[1]
                    )
                ],
                reasoning_trace=[
                    "Запрос содержит два действия: получение данных и отправку email",
                    "Нужен многошаговый workflow",
                    "Шаг 2 зависит от результатов шага 1",
                    "Классифицирую как complex_workflow"
                ]
            )
        
        elif "найди" in user_query.lower() or "поиск" in user_query.lower():
            # Простое использование инструментов
            return HybridPlanningReasoning(
                query_analysis=QueryAnalysis(
                    user_query=user_query,
                    query_type="информационный_поиск",
                    key_entities=["поиск", "информация"],
                    intent="найти_информацию"
                ),
                action_classification="use_tools",
                complexity_assessment="средняя - требует поиска в интернете",
                workflow_steps=[
                    WorkflowStep(
                        step_number=1,
                        action_type=ActionType.USE_TOOLS,
                        description="Поиск информации в интернете",
                        tool_plans=[
                            ToolPlan(
                                tool_name="web_search",
                                parameters={"query": user_query, "max_results": 5},
                                purpose="найти_актуальную_информацию",
                                expected_output="список_релевантных_результатов"
                            )
                        ]
                    )
                ],
                reasoning_trace=[
                    "Пользователь просит найти информацию",
                    "Нужен поиск в интернете",
                    "Достаточно одного шага с web_search"
                ]
            )
        
        else:
            # Прямой ответ без инструментов
            return HybridPlanningReasoning(
                query_analysis=QueryAnalysis(
                    user_query=user_query,
                    query_type="общий_вопрос",
                    key_entities=[],
                    intent="получить_общую_информацию"
                ),
                action_classification="direct_response",
                complexity_assessment="низкая - можно ответить без инструментов",
                workflow_steps=[],
                reasoning_trace=[
                    "Запрос не требует внешних данных",
                    "Можно дать прямой ответ",
                    "Инструменты не нужны"
                ]
            )
    
    def _simulate_processing_reasoning(self, user_query: str, tool_results: List[ToolExecutionResult]) -> ResultProcessingReasoning:
        """Симулирует SGR обработку результатов"""
        
        if not tool_results:
            return ResultProcessingReasoning(
                tool_results_analysis=["Инструменты не использовались"],
                data_integration="Интеграция данных не требуется",
                quality_assessment="Качество не оценивается - прямой ответ",
                completeness_check="Ответ полный без дополнительных данных",
                reasoning_trace=["Обработка результатов не требуется"]
            )
        
        analysis = []
        for result in tool_results:
            if result.success:
                analysis.append(f"{result.tool_name}: успешно выполнен, получены валидные данные")
            else:
                analysis.append(f"{result.tool_name}: ошибка выполнения")
        
        return ResultProcessingReasoning(
            tool_results_analysis=analysis,
            data_integration="Данные интегрированы последовательно согласно workflow",
            quality_assessment="Высокое качество - все инструменты выполнены успешно",
            completeness_check="Данные достаточны для полного ответа на запрос",
            reasoning_trace=[
                "Проанализировал результаты каждого инструмента",
                "Все данные получены успешно",
                "Интеграция прошла без конфликтов",
                "Ответ можно формировать"
            ]
        )
    
    def _generate_final_response(self, user_query: str, tool_results: List[ToolExecutionResult], processing: ResultProcessingReasoning) -> str:
        """Генерирует финальный ответ"""
        
        if not tool_results:
            return f"На ваш запрос '{user_query}' могу ответить напрямую без использования дополнительных инструментов."
        
        response_parts = [f"Обработал ваш запрос '{user_query}' с помощью следующих инструментов:"]
        
        for result in tool_results:
            if result.success:
                if result.tool_name == "database_query":
                    data = result.result.get("data", [])
                    response_parts.append(f"📊 База данных: найдено {len(data)} записей")
                elif result.tool_name == "web_search":
                    results = result.result.get("results", [])
                    response_parts.append(f"🔍 Веб-поиск: найдено {len(results)} результатов")
                elif result.tool_name == "send_email":
                    response_parts.append(f"📧 Email отправлен на {result.parameters.get('to')}")
        
        response_parts.append(f"\nОценка качества: {processing.quality_assessment}")
        return "\n".join(response_parts)

# Демонстрация
if __name__ == "__main__":
    # Настройка
    tool_manager = ToolManager()
    tool_manager.register_tool(WebSearchTool())
    tool_manager.register_tool(DatabaseTool())
    tool_manager.register_tool(EmailTool())
    
    agent = HybridAgent(tool_manager)
    
    # Тестовые запросы разной сложности
    test_queries = [
        "Получи данные по всем проектам и отправь отчет менеджеру на email",
        "Найди информацию о новых фреймворках для фронтенда",
        "Привет, как дела?"
    ]
    
    print("=== ГИБРИДНЫЙ ПОДХОД: SGR + FUNCTION CALLING ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"ПРИМЕР {i}: {query}")
        print("=" * 80)
        
        result = agent.process_query(query)
        
        print(f"\nПЛАНИРОВАНИЕ:")
        print(f"- Тип действия: {result.planning_reasoning.action_classification}")
        print(f"- Сложность: {result.planning_reasoning.complexity_assessment}")
        print(f"- Шагов в workflow: {len(result.planning_reasoning.workflow_steps)}")
        
        if result.tool_executions:
            print(f"\nВЫПОЛНЕНИЕ:")
            for execution in result.tool_executions:
                status = "✅" if execution.success else "❌"
                print(f"- {status} {execution.tool_name} ({execution.execution_time})")
        
        print(f"\nОБРАБОТКА:")
        print(f"- Качество: {result.processing_reasoning.quality_assessment}")
        
        print(f"\nФИНАЛЬНЫЙ ОТВЕТ:")
        print(result.final_response)
        
        print(f"\nУВЕРЕННОСТЬ: {result.confidence_score}")
        print("\n" + "="*80 + "\n")
    
    # Пример детального лога
    print("=== ДЕТАЛЬНЫЙ ЛОГ ПОСЛЕДНЕГО ЗАПРОСА ===")
    result = agent.process_query(test_queries[0])
    print(result.model_dump_json(ensure_ascii=False, indent=2))