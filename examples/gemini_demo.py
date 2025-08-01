#!/usr/bin/env python3
"""
gemini_demo.py
==============

Демонстрация возможностей Gemini CLI в MAC системе.
Показывает как использовать Gemini как инструмент и как агента.
"""

import asyncio
import os
from pathlib import Path

# Добавляем корневую директорию в путь
import sys
sys.path.append(str(Path(__file__).parent.parent))

from tools.gemini_cli import get_gemini_cli
from tools.gemini_tool import create_gemini_tools
from agents.gemini_assistant import create_gemini_assistant
from tools.logging_setup import setup_logging


async def demo_direct_cli():
    """Демонстрация прямого использования Gemini CLI."""
    print("\n=== Демонстрация прямого использования Gemini CLI ===\n")
    
    gemini = get_gemini_cli()
    
    # Простой запрос
    print("1. Простой запрос к Gemini:")
    result = await gemini.execute("Explain what is a Multi-Agent System in 3 sentences")
    if result["success"]:
        print(f"Ответ: {result['response'][:200]}...")
    else:
        print(f"Ошибка: {result['error']}")
    
    # Анализ кода
    print("\n2. Анализ кода системы:")
    if Path("run_system.py").exists():
        result = await gemini.analyze_code("run_system.py", "general")
        if result["success"]:
            print(f"Анализ: {result['response'][:300]}...")
    
    # Исследование с Google Search
    print("\n3. Исследование актуальной темы:")
    result = await gemini.research("Latest developments in Multi-Agent Systems 2025")
    if result["success"]:
        print(f"Исследование: {result['response'][:300]}...")


def demo_as_tool():
    """Демонстрация использования Gemini как инструмента."""
    print("\n=== Демонстрация Gemini как инструмента ===\n")
    
    tools = create_gemini_tools()
    
    # Помощь с кодом
    print("1. Помощь с написанием кода:")
    result = tools["gemini_code_assist"](
        "Write a Python function to manage agent communication in a multi-agent system"
    )
    print(f"Код: {result[:400]}...")
    
    # Генерация тестов
    print("\n2. Генерация тестов:")
    if Path("tools/gemini_cli.py").exists():
        result = tools["gemini_generate_tests"]("tools/gemini_cli.py")
        print(f"Тесты: {result[:400]}...")
    
    # Отладка ошибки
    print("\n3. Помощь с отладкой:")
    error = "AttributeError: 'NoneType' object has no attribute 'execute'"
    result = tools["gemini_debug_error"](error, ["tools/gemini_cli.py"])
    print(f"Решение: {result[:400]}...")


async def demo_as_agent():
    """Демонстрация работы специализированного агента Gemini."""
    print("\n=== Демонстрация Gemini Assistant как агента ===\n")
    
    # Создаем агента
    gemini_agent = create_gemini_assistant()
    
    print(f"Создан агент: {gemini_agent.name}")
    print(f"Системное сообщение: {gemini_agent.system_message[:200]}...")
    
    # В реальной системе агент будет работать через AutoGen GroupChat
    # Здесь показываем его конфигурацию
    print("\nВозможности агента:")
    from agents.gemini_assistant import GEMINI_ASSISTANT_CONFIG
    for capability in GEMINI_ASSISTANT_CONFIG["capabilities"]:
        print(f"  - {capability}")


def main():
    """Основная функция демонстрации."""
    # Настраиваем логирование
    setup_logging()
    
    print("🚀 Демонстрация интеграции Gemini CLI в MAC систему")
    print("=" * 60)
    
    # Проверяем наличие Gemini CLI
    import subprocess
    try:
        result = subprocess.run(["gemini", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Gemini CLI установлен: {result.stdout.strip()}")
        else:
            print("❌ Gemini CLI не найден. Установите: npm install -g @google/gemini-cli")
            return
    except FileNotFoundError:
        print("❌ Gemini CLI не найден. Установите: npm install -g @google/gemini-cli")
        return
    
    # Запускаем демонстрации
    asyncio.run(demo_direct_cli())
    demo_as_tool()
    asyncio.run(demo_as_agent())
    
    print("\n" + "=" * 60)
    print("✅ Демонстрация завершена!")
    print("\nДля использования в продакшене:")
    print("1. Настройте GEMINI_API_KEY или войдите через Google аккаунт")
    print("2. Добавьте Gemini tools в нужные агенты")
    print("3. Или используйте специализированного Gemini Assistant")


if __name__ == "__main__":
    main()