#!/usr/bin/env python3
"""Тесты исправленной MAS системы"""

import traceback
import sys
import os
from pathlib import Path

# Добавляем корневую папку в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_agents_creation():
    """Тест создания агентов"""
    print("\n🧪 Тест создания агентов...")
    
    try:
        from agents.core_agents import create_agents
        from config.config_loader import AgentsConfig
        
        # Загружаем конфигурацию
        cfg = AgentsConfig.from_yaml("config/agents.yaml")
        
        # Создаем агентов
        agents = create_agents(cfg)
        
        print(f"✅ Создано агентов: {len(agents)}")
        for name, agent in agents.items():
            print(f"  - {name}: {type(agent).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания агентов: {e}")
        traceback.print_exc()
        return False

def test_smart_groupchat():
    """Тест Smart GroupChat Manager"""
    print("\n🧪 Тест Smart GroupChat Manager...")
    
    try:
        from tools.smart_groupchat import SmartGroupChatManager
        from agents.core_agents import create_agents
        from config.config_loader import AgentsConfig
        
        # Создаем агентов
        cfg = AgentsConfig.from_yaml("config/agents.yaml")
        agents = create_agents(cfg)
        
        # Простая маршрутизация
        routing = {
            "meta": ["coordination"],
            "coordination": []
        }
        
        # Создаем manager
        manager = SmartGroupChatManager(agents, routing)
        
        # Тестируем отправку сообщения
        response = manager.process_user_message("Тестовое сообщение")
        print(f"📨 Ответ: {response}")
        
        print("✅ Smart GroupChat Manager работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка Smart GroupChat Manager: {e}")
        traceback.print_exc()
        return False

def test_base_agent_hash():
    """Тест хэшируемости BaseAgent"""
    print("\n🧪 Тест хэшируемости BaseAgent...")
    
    try:
        from agents.base import BaseAgent
        
        agent1 = BaseAgent("test1", {})
        agent2 = BaseAgent("test2", {})
        
        # Тестируем хэш
        hash1 = hash(agent1)
        hash2 = hash(agent2)
        
        # Тестируем равенство
        assert agent1 == agent1
        assert agent1 != agent2
        
        # Тестируем использование в set
        agent_set = {agent1, agent2}
        assert len(agent_set) == 2
        
        print("✅ BaseAgent хэшируется корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка хэширования BaseAgent: {e}")
        traceback.print_exc()
        return False

def main():
    """Запуск всех тестов"""
    print("🚀 Запуск тестов исправленной MAS системы")
    print("=" * 50)
    
    tests = [
        test_agents_creation,
        test_smart_groupchat, 
        test_base_agent_hash
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Критическая ошибка в {test.__name__}: {e}")
    
    print(f"\n📊 Результат: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно!")
        return True
    else:
        print("⚠️ Есть проваленные тесты")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)