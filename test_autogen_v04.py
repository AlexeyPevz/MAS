#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы агентов после миграции на AutoGen v0.4
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.core_agents import create_agents
from config.config_loader import load_config


def test_agent_creation():
    """Тест создания агентов"""
    print("=== Тест 1: Создание агентов ===")
    try:
        config = load_config()
        agents_config = config.get("agents", {})
        
        agents = create_agents(agents_config)
        print(f"✅ Создано агентов: {len(agents)}")
        for name, agent in agents.items():
            print(f"  - {name}: {type(agent).__name__}")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания агентов: {e}")
        return False


def test_generate_reply():
    """Тест метода generate_reply"""
    print("\n=== Тест 2: Метод generate_reply ===")
    try:
        from agents.base import BaseAgent
        
        # Создаем тестового агента
        agent = BaseAgent("test_agent", model="gpt-3.5-turbo", tier="cheap")
        
        # Тестовое сообщение
        messages = [{"content": "Привет, как дела?", "name": "user"}]
        
        # Вызываем generate_reply (синхронный для совместимости)
        response = agent.generate_reply(messages)
        print(f"✅ Ответ получен: {response[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Ошибка generate_reply: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_interaction():
    """Тест асинхронного взаимодействия"""
    print("\n=== Тест 3: Асинхронное взаимодействие ===")
    try:
        from agents.base import BaseAgent
        
        # Создаем агента
        agent = BaseAgent("async_test", model="gpt-3.5-turbo", tier="cheap")
        
        # Тестовое сообщение
        messages = [{"content": "Тест асинхронного вызова", "name": "user"}]
        
        # Вызываем асинхронный метод
        response = await agent.generate_reply_async(messages)
        print(f"✅ Асинхронный ответ: {response[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Ошибка async взаимодействия: {e}")
        return False


def test_smart_groupchat():
    """Тест SmartGroupChatManager"""
    print("\n=== Тест 4: SmartGroupChatManager ===")
    try:
        from tools.smart_groupchat import SmartGroupChatManager
        
        manager = SmartGroupChatManager()
        print("✅ SmartGroupChatManager создан")
        
        # Проверяем, что manager может инициализироваться
        asyncio.run(manager.initialize())
        print("✅ Manager инициализирован")
        return True
    except Exception as e:
        print(f"❌ Ошибка SmartGroupChatManager: {e}")
        return False


async def main():
    """Запуск всех тестов"""
    print("🔧 Тестирование системы после миграции на AutoGen v0.4\n")
    
    # Проверяем наличие API ключа
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  OPENROUTER_API_KEY не установлен, некоторые тесты могут не работать")
    
    results = []
    
    # Тест 1: Создание агентов
    results.append(("Создание агентов", test_agent_creation()))
    
    # Тест 2: generate_reply
    results.append(("generate_reply", test_generate_reply()))
    
    # Тест 3: Асинхронное взаимодействие
    result = await test_async_interaction()
    results.append(("Асинхронное взаимодействие", result))
    
    # Тест 4: SmartGroupChatManager
    results.append(("SmartGroupChatManager", test_smart_groupchat()))
    
    # Итоги
    print("\n=== ИТОГИ ТЕСТИРОВАНИЯ ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nВсего тестов: {total}, Пройдено: {passed}")
    
    if passed == total:
        print("\n🎉 Все тесты пройдены! Система готова к работе.")
    else:
        print(f"\n⚠️  {total - passed} тестов не пройдено. Проверьте логи выше.")


if __name__ == "__main__":
    asyncio.run(main())