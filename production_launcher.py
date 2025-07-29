#!/usr/bin/env python3
"""
Production MAS System Launcher
Полноценный launcher для production развертывания
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

# Настройка путей
sys.path.insert(0, str(Path(__file__).parent))

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback - загружаем .env вручную
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    else:
        print("⚠️ .env файл не найден, используем системные переменные")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/mas_production.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def validate_environment() -> bool:
    """Валидация переменных окружения"""
    logger.info("🔍 Проверка окружения...")
    
    required_vars = [
        'OPENROUTER_API_KEY',
    ]
    
    optional_vars = [
        'YANDEX_GPT_API_KEY',
        'YANDEX_FOLDER_ID', 
        'TELEGRAM_BOT_TOKEN',
        'N8N_API_TOKEN',
        'POSTGRES_HOST',
        'REDIS_HOST'
    ]
    
    # Проверяем обязательные переменные
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        logger.error(f"❌ Отсутствуют обязательные переменные: {missing_required}")
        return False
    
    # Проверяем опциональные переменные
    missing_optional = []
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_optional:
        logger.warning(f"⚠️ Отсутствуют опциональные переменные: {missing_optional}")
        logger.info("💡 Некоторые функции могут быть недоступны")
    
    # Проверяем API ключи
    from tools.llm_config import validate_api_keys, get_available_models
    
    api_status = validate_api_keys()
    logger.info("🔑 Статус API ключей:")
    for provider, available in api_status.items():
        status = "✅" if available else "❌"
        logger.info(f"  {status} {provider}")
    
    # Показываем доступные модели
    models = get_available_models()
    logger.info(f"🤖 Доступно моделей: {len(models)}")
    
    return True


def create_directories():
    """Создание необходимых директорий"""
    directories = [
        'logs',
        'data',
        'backups',
        'temp'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"📁 Создана директория: {directory}")


async def initialize_agents() -> Dict[str, Any]:
    """Инициализация всех агентов системы"""
    logger.info("🤖 Инициализация агентов...")
    
    try:
        from pathlib import Path
        from agents.core_agents import create_agents
        from config_loader import AgentsConfig
        
        # Загружаем конфигурацию агентов
        config_path = Path('config/agents.yaml')
        config = AgentsConfig.from_yaml(config_path)
        
        # Создаем агентов
        agents = create_agents(config)
        
        logger.info(f"✅ Создано {len(agents)} агентов:")
        for name, agent in agents.items():
            logger.info(f"  • {name}: {type(agent).__name__}")
        
        return agents
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации агентов: {e}")
        raise


def setup_routing() -> Dict[str, list]:
    """Настройка маршрутизации сообщений"""
    return {
        "communicator": ["meta"],
        "meta": ["coordination", "researcher"],
        "coordination": ["prompt_builder", "workflow_builder", "webapp_builder"],
        "researcher": ["fact_checker"],
        "fact_checker": ["meta"],
        "prompt_builder": ["model_selector"],
        "model_selector": ["agent_builder"],
        "agent_builder": ["instance_factory"],
        "multi_tool": ["workflow_builder", "webapp_builder"],
        "workflow_builder": ["multi_tool"],
        "webapp_builder": ["multi_tool"],
        "instance_factory": ["coordination"]
    }


async def start_monitoring():
    """Запуск системы мониторинга"""
    try:
        from tools.observability import start_metrics_server
        start_metrics_server()
        logger.info("📊 Prometheus metrics доступны на порту 9000")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось запустить мониторинг: {e}")


async def start_telegram_bot(manager):
    """Запуск Telegram бота"""
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN не настроен, бот недоступен")
        return
    
    try:
        # Здесь будет интеграция с Telegram ботом
        logger.info("🤖 Telegram бот будет запущен в следующей версии")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска Telegram бота: {e}")


async def start_web_interface(manager):
    """Запуск веб-интерфейса"""
    try:
        # Здесь будет веб-интерфейс для управления
        logger.info("🌐 Веб-интерфейс будет запущен в следующей версии")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска веб-интерфейса: {e}")


class ProductionMASSystem:
    """Основной класс production MAS системы"""
    
    def __init__(self):
        self.agents = None
        self.manager = None
        self.routing = None
        self.running = False
    
    async def start(self):
        """Запуск всей системы"""
        logger.info("🚀 Запуск Production MAS System")
        logger.info("=" * 60)
        
        try:
            # Валидация окружения
            if not validate_environment():
                sys.exit(1)
            
            # Создание директорий
            create_directories()
            
            # Инициализация агентов
            self.agents = await initialize_agents()
            
            # Настройка маршрутизации
            self.routing = setup_routing()
            
            # Создание умного группового чата
            from tools.smart_groupchat import SmartGroupChatManager
            self.manager = SmartGroupChatManager(self.agents, self.routing)
            
            # Запуск мониторинга
            await start_monitoring()
            
            # Запуск дополнительных сервисов
            await start_telegram_bot(self.manager)
            await start_web_interface(self.manager)
            
            self.running = True
            
            logger.info("✅ MAS система запущена и готова к работе!")
            
            # Интерактивный режим для тестирования
            await self.interactive_mode()
            
        except KeyboardInterrupt:
            logger.info("👋 Получен сигнал завершения...")
            await self.shutdown()
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    async def interactive_mode(self):
        """Интерактивный режим для тестирования"""
        logger.info("\n🎯 Интерактивный режим запущен")
        print("\nДоступные команды:")
        print("1. Отправить сообщение")
        print("2. Статус системы")
        print("3. Статистика агентов")
        print("4. Создать задачу")
        print("5. Выход")
        
        while self.running:
            try:
                print("\n" + "="*50)
                choice = input("👉 Выберите действие (1-5): ").strip()
                
                if choice == "1":
                    message = input("💬 Введите сообщение: ").strip()
                    if message:
                        print("🔄 Обрабатываем...")
                        response = await self.manager.process_user_message(message)
                        print(f"\n🤖 Ответ: {response}")
                
                elif choice == "2":
                    status = self.manager.get_system_status()
                    print("\n📊 Статус системы:")
                    for key, value in status.items():
                        print(f"  • {key}: {value}")
                
                elif choice == "3":
                    stats = self.manager.get_agent_statistics()
                    print("\n📈 Статистика агентов:")
                    for agent, count in stats.items():
                        print(f"  • {agent}: {count} сообщений")
                
                elif choice == "4":
                    task = input("📋 Описание задачи: ").strip()
                    agent = input("🤖 Агент (или Enter для auto): ").strip() or "meta"
                    if task:
                        task_id = await self.manager.create_task(task, agent)
                        print(f"✅ Задача создана: {task_id}")
                
                elif choice == "5":
                    print("👋 Завершение работы...")
                    break
                
                else:
                    print("❌ Неверная команда")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в интерактивном режиме: {e}")
        
        await self.shutdown()
    
    async def shutdown(self):
        """Корректное завершение работы"""
        logger.info("🔄 Завершение работы системы...")
        
        self.running = False
        
        # Сохранение состояния
        if self.manager:
            summary = self.manager.get_conversation_summary()
            logger.info(f"📊 Итоговая статистика: {summary}")
        
        logger.info("✅ Система корректно завершена")


async def main():
    """Основная функция"""
    system = ProductionMASSystem()
    await system.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)