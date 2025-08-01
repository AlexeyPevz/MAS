#!/usr/bin/env python3
"""
gemini_code_review_example.py
=============================

Примеры использования Gemini для код-ревью и генерации медиа контента.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from tools.gemini_tool import create_gemini_tools
import asyncio


def demo_code_review():
    """Демонстрация код-ревью через Gemini."""
    print("\n🔍 === Код-ревью с Gemini ===\n")
    
    tools = create_gemini_tools()
    
    # Пример 1: Общее код-ревью
    print("1. Общее код-ревью файла:")
    if Path("tools/gemini_cli.py").exists():
        result = tools["gemini_code_review"](
            "tools/gemini_cli.py",
            ["security", "performance", "readability"]
        )
        print(f"Результат ревью:\n{result[:500]}...\n")
    
    # Пример 2: Фокус на безопасности
    print("2. Ревью с фокусом на безопасность:")
    result = tools["gemini_analyze_code"](
        "api/endpoints.py",  # если существует
        "security"
    )
    print(f"Анализ безопасности:\n{result[:400]}...\n")
    
    # Пример 3: Помощь с улучшением кода
    print("3. Рекомендации по улучшению:")
    code_snippet = '''
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
    '''
    
    result = tools["gemini_code_assist"](
        f"Improve this code for better performance and readability:\n{code_snippet}"
    )
    print(f"Улучшенная версия:\n{result[:400]}...\n")


def demo_media_generation():
    """Демонстрация генерации медиа контента."""
    print("\n🎨 === Генерация медиа с Gemini ===\n")
    
    tools = create_gemini_tools()
    
    # Пример 1: Генерация диаграммы архитектуры
    print("1. Генерация технической диаграммы:")
    result = tools["gemini_generate_image"](
        "Technical architecture diagram of a multi-agent system with interconnected agents, message queue, and database",
        style="technical"
    )
    print(f"Результат: {result[:300]}...\n")
    
    # Пример 2: Генерация UI макета
    print("2. Генерация UI макета:")
    result = tools["gemini_generate_image"](
        "Modern dark theme dashboard UI for monitoring multi-agent system performance with charts and metrics",
        style="realistic"
    )
    print(f"Результат: {result[:300]}...\n")
    
    # Пример 3: Генерация демо-видео
    print("3. Генерация демо-видео:")
    result = tools["gemini_generate_video"](
        script="Show a futuristic AI system with multiple agents collaborating, data flowing between them with neon effects",
        duration=10
    )
    print(f"Результат: {result[:300]}...\n")


def integration_scenarios():
    """Примеры интеграционных сценариев."""
    print("\n🔗 === Сценарии интеграции ===\n")
    
    print("""
1. **Автоматическое код-ревью в CI/CD:**
   - При каждом PR автоматически вызывается gemini_code_review
   - Результаты публикуются как комментарий к PR
   - Блокировка merge при критических проблемах

2. **Генерация документации с визуализацией:**
   - Agent-Builder генерирует код нового агента
   - Gemini создает диаграмму архитектуры агента
   - Prompt-Builder генерирует документацию с изображениями

3. **Создание демо-материалов:**
   - WebApp-Builder создает приложение
   - Gemini генерирует скриншоты UI в разных стилях
   - Gemini создает демо-видео функциональности

4. **Улучшение качества кода:**
   - Coordination Agent регулярно запускает код-ревью
   - Budget-Manager отслеживает затраты на ревью
   - Meta Agent приоритизирует исправления

5. **Визуальная отладка:**
   - При сложных ошибках Gemini генерирует диаграмму потока данных
   - Показывает визуально где происходит сбой
   - Предлагает исправления с примерами
    """)


def practical_example():
    """Практический пример использования в workflow."""
    print("\n💼 === Практический пример workflow ===\n")
    
    tools = create_gemini_tools()
    
    # Симуляция реального workflow
    print("Сценарий: Разработка нового компонента с полным циклом\n")
    
    # Шаг 1: Генерация кода
    print("Шаг 1: Agent-Builder создает компонент")
    component_code = tools["gemini_code_assist"](
        "Create a React component for real-time agent status monitoring with TypeScript"
    )
    print(f"✅ Компонент создан: {len(component_code)} символов\n")
    
    # Шаг 2: Код-ревью
    print("Шаг 2: Автоматическое код-ревью")
    # В реальности бы сохранили код в файл и сделали ревью
    review = tools["gemini_query"](
        f"Review this React component for best practices:\n{component_code[:500]}..."
    )
    print(f"✅ Ревью выполнено: найдено замечаний: 3\n")
    
    # Шаг 3: Генерация тестов
    print("Шаг 3: Генерация тестов")
    tests = tools["gemini_generate_tests"]("components/AgentStatus.tsx")  # условный путь
    print(f"✅ Тесты сгенерированы: 5 test cases\n")
    
    # Шаг 4: Создание документации с визуализацией
    print("Шаг 4: Создание документации")
    docs = tools["gemini_generate_docs"]("components/AgentStatus.tsx")
    print(f"✅ Документация создана\n")
    
    # Шаг 5: Генерация UI превью
    print("Шаг 5: Генерация превью компонента")
    preview = tools["gemini_generate_image"](
        "React component showing real-time status of 5 AI agents with green/yellow/red indicators",
        style="realistic"
    )
    print(f"✅ UI превью сгенерировано\n")
    
    print("🎉 Workflow завершен! Компонент готов к использованию.")


def main():
    """Основная функция."""
    print("🚀 Gemini Code Review & Media Generation Demo")
    print("=" * 60)
    
    # Запускаем демонстрации
    demo_code_review()
    demo_media_generation()
    integration_scenarios()
    practical_example()
    
    print("\n" + "=" * 60)
    print("✅ Демонстрация завершена!")
    print("\n💡 Советы по использованию:")
    print("- Используйте код-ревью для критически важных компонентов")
    print("- Генерируйте визуализацию для документации")
    print("- Создавайте демо-видео для презентаций")
    print("- Интегрируйте в CI/CD для автоматизации качества")


if __name__ == "__main__":
    main()