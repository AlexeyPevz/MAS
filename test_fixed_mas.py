#!/usr/bin/env python3
"""
Тест исправленной MAS системы
"""
import sys
import os
from pathlib import Path

# Добавляем текущую директорию в PATH
sys.path.insert(0, str(Path(__file__).parent))

def test_agents_creation():
    """Тест создания агентов"""
    print("🧪 Тест создания агентов...")
    
    try:
        from fixed_launcher import create_simple_agents
        agents = create_simple_agents()
        
        print(f"✅ Создано {len(agents)} агентов")
        
        # Проверяем, что все нужные агенты есть
        expected_agents = [
            "meta", "coordination", "prompt_builder", "model_selector",
            "agent_builder", "instance_factory", "researcher", "fact_checker", 
            "multitool", "wf_builder", "webapp_builder", "communicator"
        ]
        
        missing = set(expected_agents) - set(agents.keys())
        if missing:
            print(f"❌ Отсутствуют агенты: {missing}")
            return False
        
        print("✅ Все агенты созданы успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания агентов: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_groupchat_wrapper():
    """Тест GroupChat wrapper"""
    print("\n🧪 Тест GroupChat wrapper...")
    
    try:
        from fixed_launcher import create_simple_agents, setup_routing
        from tools.groupchat_wrapper import SimpleGroupChatManager
        
        # Создаем агентов и маршрутизацию
        agents = create_simple_agents()
        routing = setup_routing()
        
        # Создаем manager
        manager = SimpleGroupChatManager(agents, routing)
        
        # Тестируем отправку сообщения
        response = manager.send_user_message("Тестовое сообщение")
        print(f"📨 Ответ: {response}")
        
        # Проверяем статус
        status = manager.get_status()
        print(f"📊 Статус: {status}")
        
        print("✅ GroupChat wrapper работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка GroupChat wrapper: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_base_agent_hash():
    """Тест хеширования BaseAgent"""
    print("\n🧪 Тест хеширования BaseAgent...")
    
    try:
        # Создаем простой агент для проверки hash
        class MockAgent:
            def __init__(self, name):
                self.name = name
            
            def __hash__(self):
                return hash(self.name)
            
            def __eq__(self, other):
                if not isinstance(other, MockAgent):
                    return False
                return self.name == other.name
        
        agent1 = MockAgent("test_agent")
        agent2 = MockAgent("test_agent")
        agent3 = MockAgent("other_agent")
        
        # Проверяем хеширование
        assert hash(agent1) == hash(agent2), "Одинаковые агенты должны иметь одинаковый hash"
        assert hash(agent1) != hash(agent3), "Разные агенты должны иметь разный hash"
        
        # Проверяем равенство
        assert agent1 == agent2, "Одинаковые агенты должны быть равны"
        assert agent1 != agent3, "Разные агенты не должны быть равны"
        
        # Проверяем использование в dict
        agent_dict = {agent1: "value1", agent3: "value2"}
        assert len(agent_dict) == 2, "Словарь должен содержать 2 элемента"
        
        print("✅ Хеширование работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка хеширования: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Запуск всех тестов"""
    print("🚀 Запуск тестов исправленной MAS системы")
    print("=" * 60)
    
    tests = [
        test_agents_creation,
        test_groupchat_wrapper, 
        test_base_agent_hash
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print("-" * 40)
    
    print(f"\n📊 Результаты тестирования:")
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 Все тесты пройдены! Система готова к использованию.")
        return True
    else:
        print("\n⚠️ Некоторые тесты провалились. Требуется доработка.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)