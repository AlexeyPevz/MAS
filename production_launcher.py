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
    
    # Проверяем интеграции
    logger.info("🔗 Статус интеграций:")
    
    # GPT-Pilot
    gpt_pilot_url = os.getenv('GPT_PILOT_URL', 'http://localhost:8000')
    gpt_pilot_key = os.getenv('GPT_PILOT_API_KEY')
    status_pilot = "🔑" if gpt_pilot_key else "🔓"
    logger.info(f"  🚀 GPT-Pilot: {gpt_pilot_url} {status_pilot}")
    
    # AutoGen Studio  
    studio_url = os.getenv('AUTOGEN_STUDIO_URL', 'http://localhost:8081')
    studio_key = os.getenv('AUTOGEN_STUDIO_API_KEY')
    status_studio = "🔑" if studio_key else "🔓"
    logger.info(f"  🎬 AutoGen Studio: {studio_url} {status_studio}")
    
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
        from config.config_loader import AgentsConfig
        
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
        from tools.modern_telegram_bot import ModernTelegramBot
        
        # Создаем callback для интеграции с MAS
        async def mas_callback(message: str) -> str:
            try:
                response = await manager.process_user_message(message)
                return response or "✅ Сообщение обработано"
            except Exception as e:
                logger.error(f"❌ Ошибка MAS обработки: {e}")
                return f"😔 Произошла ошибка: {str(e)[:200]}..."
        
        # Создаем и запускаем бота
        bot = ModernTelegramBot(
            token=os.getenv('TELEGRAM_BOT_TOKEN'),
            mas_callback=mas_callback,
            enable_voice=False
        )
        
        # Запускаем в фоновой задаче
        bot_task = asyncio.create_task(bot.run())
        logger.info("🤖 Telegram бот запущен и подключен к MAS системе!")
        
        # Сохраняем ссылку на задачу
        manager._telegram_bot = bot
        manager._telegram_task = bot_task
        
    except ImportError:
        logger.warning("⚠️ python-telegram-bot не установлен, бот недоступен")
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
        self.monitoring_enabled = False
        self._telegram_bot = None
        self._telegram_task = None
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """Запуск всей системы"""
        logger.info("🚀 Запуск Production MAS System...")
        
        try:
            # Инициализация системы
            await self._initialize_system()
            
            # Запуск компонентов
            await self._start_components()
            
            logger.info("✅ Все системы запущены и готовы к работе!")
            logger.info("📝 Для остановки нажмите Ctrl+C")
            
            # Ожидание сигнала остановки
            await self._shutdown_event.wait()
            
        except KeyboardInterrupt:
            logger.info("👋 Получен сигнал остановки...")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка системы: {e}")
            raise
        finally:
            await self._cleanup()

    async def _cleanup(self):
        """Очистка ресурсов при остановке"""
        logger.info("🧹 Очистка ресурсов...")
        
        try:
            # Остановка Telegram бота
            if self._telegram_bot:
                await self._telegram_bot.shutdown()
            
            if self._telegram_task:
                self._telegram_task.cancel()
                try:
                    await self._telegram_task
                except asyncio.CancelledError:
                    pass
                    
            logger.info("✅ Очистка завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при очистке: {e}")

    def shutdown(self):
        """Инициирует graceful shutdown"""
        self._shutdown_event.set()

    async def _initialize_system(self):
        """Инициализация системы"""
        logger.info("🔧 Инициализация системы...")
        
        # Валидация окружения
        if not validate_environment():
            raise RuntimeError("Ошибка валидации окружения")
        
        # Создание директорий
        create_directories()
        
        # Инициализация агентов
        self.agents = await initialize_agents()
        
        # Настройка маршрутизации
        self.routing = setup_routing()
        
        # Создание умного группового чата
        from tools.smart_groupchat import SmartGroupChatManager
        self.manager = SmartGroupChatManager(self.agents, self.routing)
        
        self.running = True
        logger.info("✅ Система инициализирована")

    async def _start_components(self):
        """Запуск компонентов системы"""
        logger.info("🚀 Запуск компонентов...")
        
        # Запуск мониторинга
        await start_monitoring()
        
        # Запуск дополнительных сервисов
        await start_telegram_bot(self.manager)
        await start_web_interface(self.manager)
        
        logger.info("✅ Все компоненты запущены")


async def main():
    """Основная функция"""
    system = ProductionMASSystem()
    
    # Обработчик сигналов для graceful shutdown
    def signal_handler():
        logger.info("🛑 Получен сигнал остановки...")
        system.shutdown()
    
    # Регистрируем обработчики сигналов
    import signal
    if hasattr(signal, 'SIGINT'):
        signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
    
    await system.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)