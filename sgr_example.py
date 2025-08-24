"""
Schema-Guided Reasoning (SGR) Example
Демонстрация структурированного рассуждения для анализа документов
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
import json

# Схема для SGR рассуждения
class QueryAnalysis(BaseModel):
    """Анализ пользовательского запроса"""
    user_query: str = Field(description="Исходный запрос пользователя")
    query_type: str = Field(description="Тип запроса: поиск, анализ, классификация")
    key_entities: List[str] = Field(description="Ключевые сущности в запросе")
    intent: str = Field(description="Намерение пользователя")

class DocumentAnalysis(BaseModel):
    """Анализ документа"""
    document_id: str
    relevance_score: float = Field(ge=0, le=1, description="Релевантность от 0 до 1")
    key_points: List[str] = Field(description="Ключевые пункты документа")
    confidence: float = Field(ge=0, le=1, description="Уверенность в анализе")

class InformationSearch(BaseModel):
    """Стратегия поиска информации"""
    search_strategy: str = Field(description="Выбранная стратегия поиска")
    search_terms: List[str] = Field(description="Термины для поиска")
    relevant_documents: List[DocumentAnalysis] = Field(description="Найденные документы")
    coverage_assessment: str = Field(description="Оценка полноты поиска")

class QualityCheck(BaseModel):
    """Проверка качества результата"""
    completeness: float = Field(ge=0, le=1, description="Полнота ответа")
    accuracy_confidence: float = Field(ge=0, le=1, description="Уверенность в точности")
    potential_gaps: List[str] = Field(description="Возможные пробелы в анализе")
    recommendations: List[str] = Field(description="Рекомендации по улучшению")

class SGRReasoning(BaseModel):
    """Полная схема SGR рассуждения"""
    query_analysis: QueryAnalysis
    information_search: InformationSearch  
    quality_check: QualityCheck
    reasoning_trace: List[str] = Field(description="Трассировка рассуждений")

class SGRResponse(BaseModel):
    """Финальный ответ с рассуждением"""
    reasoning: SGRReasoning
    response: str = Field(description="Финальный ответ пользователю")
    confidence_score: float = Field(ge=0, le=1, description="Общая уверенность")
    metadata: Dict = Field(default_factory=dict, description="Дополнительные метаданные")

# Пример использования SGR для анализа проекта
def create_sgr_prompt(user_query: str, documents: List[Dict]) -> str:
    """Создает промпт для SGR анализа"""
    
    schema_json = SGRResponse.model_json_schema()
    
    prompt = f"""
Ты эксперт-аналитик. Проанализируй запрос пользователя и предоставь структурированный ответ.

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {user_query}

ДОСТУПНЫЕ ДОКУМЕНТЫ:
{json.dumps(documents, ensure_ascii=False, indent=2)}

Проведи анализ по следующей схеме:

1. АНАЛИЗ ЗАПРОСА (query_analysis):
   - Определи тип запроса и ключевые сущности
   - Выяви намерение пользователя

2. ПОИСК ИНФОРМАЦИИ (information_search):
   - Выбери стратегию поиска
   - Оцени релевантность каждого документа
   - Извлеки ключевые пункты

3. ПРОВЕРКА КАЧЕСТВА (quality_check):
   - Оцени полноту и точность
   - Выяви возможные пробелы
   - Дай рекомендации

4. ФИНАЛЬНЫЙ ОТВЕТ:
   - Сформулируй четкий ответ на основе анализа
   - Укажи уровень уверенности

Верни результат в формате JSON согласно схеме:

{json.dumps(schema_json, ensure_ascii=False, indent=2)}

Обязательно заполни ВСЕ поля схемы. В reasoning_trace запиши пошаговое рассуждение.
"""
    
    return prompt

# Пример документов для анализа
sample_documents = [
    {
        "id": "doc_1",
        "title": "Техническая спецификация проекта X",
        "content": "Проект X использует микросервисную архитектуру с React фронтендом...",
        "type": "technical_spec"
    },
    {
        "id": "doc_2", 
        "title": "Бизнес-требования проекта X",
        "content": "Основная цель проекта - создание платформы для электронной коммерции...",
        "type": "business_requirements"
    },
    {
        "id": "doc_3",
        "title": "Архитектурные решения",
        "content": "Для обеспечения масштабируемости выбран подход с контейнеризацией...",
        "type": "architecture"
    }
]

# Демонстрация
if __name__ == "__main__":
    user_query = "Найди информацию о техническом стеке проекта X и его масштабируемости"
    
    # Создаем промпт для SGR
    sgr_prompt = create_sgr_prompt(user_query, sample_documents)
    
    print("=== SGR PROMPT ===")
    print(sgr_prompt)
    print("\n" + "="*50)
    
    # Пример ожидаемого структурированного ответа
    expected_response = SGRResponse(
        reasoning=SGRReasoning(
            query_analysis=QueryAnalysis(
                user_query=user_query,
                query_type="технический_поиск",
                key_entities=["технический стек", "проект X", "масштабируемость"],
                intent="получить_техническую_информацию"
            ),
            information_search=InformationSearch(
                search_strategy="поиск_по_техническим_ключевым_словам",
                search_terms=["технический стек", "архитектура", "масштабируемость"],
                relevant_documents=[
                    DocumentAnalysis(
                        document_id="doc_1",
                        relevance_score=0.9,
                        key_points=["микросервисная архитектура", "React фронтенд"],
                        confidence=0.95
                    ),
                    DocumentAnalysis(
                        document_id="doc_3", 
                        relevance_score=0.8,
                        key_points=["контейнеризация", "масштабируемость"],
                        confidence=0.9
                    )
                ],
                coverage_assessment="хорошее_покрытие_технических_аспектов"
            ),
            quality_check=QualityCheck(
                completeness=0.85,
                accuracy_confidence=0.9,
                potential_gaps=["отсутствует информация о базе данных"],
                recommendations=["найти дополнительную документацию по БД"]
            ),
            reasoning_trace=[
                "Проанализировал запрос - пользователь ищет техническую информацию",
                "Определил ключевые термины для поиска",
                "Нашел 2 релевантных документа из 3",
                "Извлек информацию о React, микросервисах и контейнеризации",
                "Выявил пробел в информации о базе данных"
            ]
        ),
        response="Проект X использует следующий технический стек: React для фронтенда, микросервисная архитектура для бэкенда. Для обеспечения масштабируемости применяется контейнеризация. Однако в документации не хватает информации о выборе базы данных.",
        confidence_score=0.85,
        metadata={
            "processing_time": "simulated",
            "documents_analyzed": 3,
            "relevant_documents": 2
        }
    )
    
    print("=== ПРИМЕР СТРУКТУРИРОВАННОГО ОТВЕТА ===")
    print(expected_response.model_dump_json(ensure_ascii=False, indent=2))