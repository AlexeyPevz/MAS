#!/usr/bin/env python3
"""
Fixed MAS System Launcher
Использует SimpleGroupChatManager для обхода проблем совместимости
"""
import os
import sys
import logging
from typing import Dict, Any
from pathlib import Path

# Настройка путей
sys.path.insert(0, str(Path(__file__).parent))

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv не установлен, используем системные переменные")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def check_environment() -> bool:
    """Проверка API ключей"""
    required_keys = ['OPENROUTER_API_KEY']
    
    missing = []
    for key in required_keys:
        if not os.getenv(key):
            missing.append(key)
    
    if missing:
        logger.warning(f"⚠️ Отсутствуют API ключи: {missing}")
        logger.info("💡 Система будет работать в demo режиме")
        return True  # Не блокируем запуск
    
    logger.info("✅ API ключи настроены")
    return True


def create_simple_agents() -> Dict[str, Any]:
    """Создание упрощенных агентов без сложных зависимостей"""
    
    class SimpleAgent:
        def __init__(self, name: str, role: str):
            self.name = name
            self.role = role
            self.system_message = f"Вы - {role} агент. Ваша задача: {self._get_role_description(role)}"
        
        def _get_role_description(self, role: str) -> str:
            descriptions = {
                "Meta": "координация работы всех агентов и планирование задач",
                "Coordination": "управление очередью задач и их статусами", 
                "PromptBuilder": "создание и оптимизация промптов для агентов",
                "ModelSelector": "выбор оптимальных LLM моделей для задач",
                "AgentBuilder": "создание новых агентов по спецификациям",
                "InstanceFactory": "развертывание новых MAS инстансов",
                "Researcher": "поиск и анализ информации в интернете",
                "FactChecker": "проверка достоверности информации и фактов", 
                "MultiTool": "интеграция с внешними API и сервисами",
                "WfBuilder": "создание n8n workflow для автоматизации",
                "WebAppBuilder": "разработка веб-приложений через GPT-Pilot",
                "Communicator": "взаимодействие с пользователями через различные интерфейсы"
            }
            return descriptions.get(role, "выполнение специализированных задач")
        
        def generate_reply(self, messages=None, sender=None, config=None):
            return f"[{self.role}] Сообщение обработано агентом {self.name}"
    
    agents = {}
    
    # Создаем всех 12 агентов согласно config/agents.yaml
    agent_configs = [
        ("meta", "Meta"),
        ("coordination", "Coordination"), 
        ("prompt_builder", "PromptBuilder"),
        ("model_selector", "ModelSelector"),
        ("agent_builder", "AgentBuilder"),
        ("instance_factory", "InstanceFactory"),
        ("researcher", "Researcher"),
        ("fact_checker", "FactChecker"),
        ("multitool", "MultiTool"),
        ("wf_builder", "WfBuilder"),
        ("webapp_builder", "WebAppBuilder"),
        ("communicator", "Communicator")
    ]
    
    for name, role in agent_configs:
        agents[name] = SimpleAgent(name, role)
        logger.info(f"✅ Создан агент: {name} ({role})")
    
    return agents


def setup_routing() -> Dict[str, list]:
    """Настройка маршрутизации согласно архитектуре"""
    return {
        "communicator": ["meta"],
        "meta": ["coordination", "researcher"],
        "coordination": ["prompt_builder", "wf_builder", "webapp_builder"],
        "researcher": ["fact_checker"],
        "fact_checker": ["meta"],
        "prompt_builder": ["model_selector"],
        "model_selector": ["agent_builder"],
        "agent_builder": ["instance_factory"],
        "multitool": ["wf_builder", "webapp_builder"],
        "wf_builder": ["multitool"],
        "webapp_builder": ["multitool"],
        "instance_factory": ["coordination"]
    }


def main():
    """Основная функция запуска"""
    print("\n🚀 MAS System - Fixed Launcher")
    print("=" * 50)
    
    # Проверяем окружение
    if not check_environment():
        sys.exit(1)
    
    try:
        # Создаем агентов
        print("\n🤖 Создание агентов...")
        agents = create_simple_agents()
        
        # Настраиваем маршрутизацию
        routing = setup_routing()
        
        # Импортируем наш wrapper manager
        from tools.groupchat_wrapper import SimpleGroupChatManager
        
        # Создаем manager
        manager = SimpleGroupChatManager(agents, routing)
        
        print(f"\n✅ MAS система запущена!")
        print(f"📊 Агентов: {len(agents)}")
        print(f"🔀 Маршрутов: {len(routing)}")
        
        # Интерактивный режим
        while True:
            print("\n" + "="*50)
            print("🎯 Доступные команды:")
            print("1. Отправить сообщение в MAS")
            print("2. Показать статус системы")
            print("3. Показать агентов")
            print("4. Выход")
            
            choice = input("\n👉 Выберите действие (1-4): ").strip()
            
            if choice == "1":
                message = input("\n💬 Введите сообщение: ").strip()
                if message:
                    response = manager.send_user_message(message)
                    print(f"\n🔄 Результат: {response}")
                    
            elif choice == "2":
                status = manager.get_status()
                print(f"\n📊 Статус системы:")
                for key, value in status.items():
                    print(f"  • {key}: {value}")
                    
            elif choice == "3":
                print(f"\n🤖 Список агентов:")
                for name, agent in agents.items():
                    print(f"  • {name}: {agent.role}")
                    
            elif choice == "4":
                print("\n👋 Завершение работы...")
                break
                
            else:
                print("❌ Неверная команда")
                
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        print("\n💡 Для полной функциональности установите:")
        print("pip install autogen openai python-dotenv")
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()