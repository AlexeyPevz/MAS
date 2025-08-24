"""
Упрощенная демонстрация SGR без внешних зависимостей
"""

import json
from typing import Dict, List, Any
from dataclasses import dataclass, field

# Простые dataclasses вместо Pydantic
@dataclass
class QueryAnalysis:
    user_query: str
    query_type: str
    key_entities: List[str]
    intent: str

@dataclass
class DocumentAnalysis:
    document_id: str
    relevance_score: float
    key_points: List[str]
    confidence: float

@dataclass
class InformationSearch:
    search_strategy: str
    search_terms: List[str]
    relevant_documents: List[DocumentAnalysis]
    coverage_assessment: str

@dataclass
class QualityCheck:
    completeness: float
    accuracy_confidence: float
    potential_gaps: List[str]
    recommendations: List[str]

@dataclass
class SGRReasoning:
    query_analysis: QueryAnalysis
    information_search: InformationSearch
    quality_check: QualityCheck
    reasoning_trace: List[str] = field(default_factory=list)

@dataclass
class SGRResponse:
    reasoning: SGRReasoning
    response: str
    confidence_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

# Демонстрация SGR
def demonstrate_sgr():
    print("=== SCHEMA-GUIDED REASONING ДЕМОНСТРАЦИЯ ===\n")
    
    # Пример документов
    documents = [
        {
            "id": "doc_1",
            "title": "Техническая спецификация проекта X",
            "content": "Проект X использует микросервисную архитектуру с React фронтендом, Node.js бэкендом и PostgreSQL базой данных. Система поддерживает горизонтальное масштабирование через Docker контейнеры.",
            "type": "technical_spec"
        },
        {
            "id": "doc_2", 
            "title": "Бизнес-требования проекта X",
            "content": "Основная цель проекта - создание платформы для электронной коммерции с поддержкой до 10000 одновременных пользователей. Требования к доступности: 99.9%.",
            "type": "business_requirements"
        },
        {
            "id": "doc_3",
            "title": "Архитектурные решения",
            "content": "Для обеспечения масштабируемости выбран подход с контейнеризацией и оркестрацией через Kubernetes. Используется microservices паттерн с API Gateway.",
            "type": "architecture"
        }
    ]
    
    user_query = "Найди информацию о техническом стеке проекта X и его масштабируемости"
    
    print(f"ПОЛЬЗОВАТЕЛЬСКИЙ ЗАПРОС: {user_query}\n")
    
    # Симуляция SGR рассуждения
    print("1. АНАЛИЗ ЗАПРОСА:")
    query_analysis = QueryAnalysis(
        user_query=user_query,
        query_type="технический_поиск",
        key_entities=["технический стек", "проект X", "масштабируемость"],
        intent="получить_техническую_информацию"
    )
    print(f"   - Тип запроса: {query_analysis.query_type}")
    print(f"   - Ключевые сущности: {query_analysis.key_entities}")
    print(f"   - Намерение: {query_analysis.intent}\n")
    
    print("2. ПОИСК ИНФОРМАЦИИ:")
    # Анализ релевантности документов
    relevant_docs = []
    
    for doc in documents:
        # Простая оценка релевантности
        content_lower = doc["content"].lower()
        relevance = 0.0
        key_points = []
        
        if "стек" in user_query.lower() or "технический" in user_query.lower():
            if any(tech in content_lower for tech in ["react", "node.js", "postgresql", "docker"]):
                relevance += 0.4
                if "react" in content_lower: key_points.append("React фронтенд")
                if "node.js" in content_lower: key_points.append("Node.js бэкенд") 
                if "postgresql" in content_lower: key_points.append("PostgreSQL база данных")
                if "docker" in content_lower: key_points.append("Docker контейнеры")
        
        if "масштабируемость" in user_query.lower():
            if any(scale in content_lower for scale in ["масштабирование", "kubernetes", "microservices"]):
                relevance += 0.5
                if "масштабирование" in content_lower: key_points.append("Горизонтальное масштабирование")
                if "kubernetes" in content_lower: key_points.append("Kubernetes оркестрация")
                if "microservices" in content_lower: key_points.append("Микросервисная архитектура")
        
        if relevance > 0.3:  # Порог релевантности
            doc_analysis = DocumentAnalysis(
                document_id=doc["id"],
                relevance_score=min(relevance, 1.0),
                key_points=key_points,
                confidence=0.9 if relevance > 0.7 else 0.7
            )
            relevant_docs.append(doc_analysis)
    
    search_info = InformationSearch(
        search_strategy="поиск_по_техническим_ключевым_словам",
        search_terms=["технический стек", "масштабируемость", "архитектура"],
        relevant_documents=relevant_docs,
        coverage_assessment="хорошее_покрытие_технических_аспектов"
    )
    
    print(f"   - Стратегия: {search_info.search_strategy}")
    print(f"   - Найдено релевантных документов: {len(relevant_docs)}")
    for doc in relevant_docs:
        print(f"     * {doc.document_id} (релевантность: {doc.relevance_score:.1f})")
        for point in doc.key_points:
            print(f"       - {point}")
    print()
    
    print("3. ПРОВЕРКА КАЧЕСТВА:")
    
    # Оценка полноты
    tech_coverage = any("react" in str(doc.key_points).lower() for doc in relevant_docs)
    scale_coverage = any("масштабирование" in str(doc.key_points).lower() for doc in relevant_docs)
    completeness = (0.5 if tech_coverage else 0) + (0.5 if scale_coverage else 0)
    
    quality_check = QualityCheck(
        completeness=completeness,
        accuracy_confidence=0.9,
        potential_gaps=["отсутствует информация о мониторинге"] if completeness < 1.0 else [],
        recommendations=["найти дополнительную документацию по DevOps"] if completeness < 1.0 else ["информации достаточно"]
    )
    
    print(f"   - Полнота: {quality_check.completeness:.1f}")
    print(f"   - Уверенность в точности: {quality_check.accuracy_confidence:.1f}")
    if quality_check.potential_gaps:
        print(f"   - Возможные пробелы: {quality_check.potential_gaps}")
    print(f"   - Рекомендации: {quality_check.recommendations}\n")
    
    # Формирование финального ответа
    tech_stack_info = []
    scalability_info = []
    
    for doc in relevant_docs:
        for point in doc.key_points:
            if any(tech in point.lower() for tech in ["react", "node.js", "postgresql", "docker"]):
                tech_stack_info.append(point)
            elif any(scale in point.lower() for scale in ["масштабирование", "kubernetes", "микросервис"]):
                scalability_info.append(point)
    
    response_parts = ["На основе анализа документации проекта X:"]
    
    if tech_stack_info:
        response_parts.append(f"\nТехнический стек:")
        for info in tech_stack_info:
            response_parts.append(f"• {info}")
    
    if scalability_info:
        response_parts.append(f"\nМасштабируемость:")
        for info in scalability_info:
            response_parts.append(f"• {info}")
    
    final_response = "\n".join(response_parts)
    
    # Создание полного SGR ответа
    reasoning_trace = [
        "Проанализировал запрос - пользователь ищет техническую информацию о проекте X",
        "Определил ключевые термины: технический стек, масштабируемость",
        f"Нашел {len(relevant_docs)} релевантных документа из {len(documents)}",
        "Извлек информацию о технологиях и архитектурных решениях",
        "Оценил полноту информации и выявил возможные пробелы"
    ]
    
    sgr_reasoning = SGRReasoning(
        query_analysis=query_analysis,
        information_search=search_info,
        quality_check=quality_check,
        reasoning_trace=reasoning_trace
    )
    
    sgr_response = SGRResponse(
        reasoning=sgr_reasoning,
        response=final_response,
        confidence_score=quality_check.completeness * quality_check.accuracy_confidence,
        metadata={
            "processing_method": "SGR",
            "documents_analyzed": len(documents),
            "relevant_documents": len(relevant_docs),
            "tech_stack_covered": bool(tech_stack_info),
            "scalability_covered": bool(scalability_info)
        }
    )
    
    print("4. ФИНАЛЬНЫЙ ОТВЕТ:")
    print(final_response)
    print(f"\nУВЕРЕННОСТЬ: {sgr_response.confidence_score:.2f}")
    
    print("\n" + "="*60)
    print("ТРАССИРОВКА РАССУЖДЕНИЙ:")
    for i, trace in enumerate(reasoning_trace, 1):
        print(f"{i}. {trace}")
    
    print("\n" + "="*60)
    print("ПРЕИМУЩЕСТВА SGR В ЭТОМ ПРИМЕРЕ:")
    print("✅ Все шаги рассуждения видны и логируются")
    print("✅ Можно точно понять, почему выбраны именно эти документы")
    print("✅ Качество ответа можно оценить по метрикам (completeness, confidence)")
    print("✅ Легко отладить и улучшить процесс")
    print("✅ Предсказуемый результат для одинаковых входных данных")
    
    return sgr_response

if __name__ == "__main__":
    result = demonstrate_sgr()
    
    print("\n" + "="*60)
    print("СТРУКТУРИРОВАННЫЙ РЕЗУЛЬТАТ (для мониторинга):")
    
    # Сериализация результата для логирования
    def to_dict(obj):
        if hasattr(obj, '__dict__'):
            return {key: to_dict(value) for key, value in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [to_dict(item) for item in obj]
        else:
            return obj
    
    result_dict = to_dict(result)
    print(json.dumps(result_dict, ensure_ascii=False, indent=2))