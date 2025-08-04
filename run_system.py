#!/usr/bin/env python3
"""
Root-MAS System Launcher
Запуск всей системы: API + MAS + Telegram Bot
"""

import os
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Загружаем переменные окружения из .env файла
from dotenv import load_dotenv
load_dotenv()


async def main():
    """Главная функция запуска системы"""
    
    # Настройка логирования с ротацией
    from tools.logging_config import setup_production_logging, setup_development_logging, log_monitor
    
    environment = os.getenv("ENVIRONMENT", "production")
    if environment == "production":
        setup_production_logging()
    else:
        setup_development_logging()
    
    # Проверяем размер логов
    log_monitor()
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Запуск Root-MAS System...")
    
    try:
        # Создаем директории
        os.makedirs("logs", exist_ok=True)
        
        # Проверяем переменные окружения
        required_vars = ["OPENROUTER_API_KEY"]
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Отсутствуют переменные окружения: {missing_vars}")
            sys.exit(1)
        
        # Определяем режим запуска
        mode = os.getenv("RUN_MODE", "full")  # full, api, mas
        
        tasks = []
        
        if mode in ["full", "api"]:
            # Запуск API сервера
            logger.info("🌐 Запуск API сервера...")
            api_task = asyncio.create_task(run_api_server())
            tasks.append(("API Server", api_task))
        
        if mode in ["full", "mas"]:
            # Запуск MAS системы (если нужен отдельно)
            logger.info("🤖 MAS система будет запущена через API...")
        
        if mode == "full" and os.getenv("TELEGRAM_BOT_TOKEN"):
            # Запуск Telegram бота (через API)
            logger.info("📱 Запуск Telegram бота...")
            bot_task = asyncio.create_task(run_telegram_bot_wrapper())
            tasks.append(("Telegram Bot", bot_task))
        
        if not tasks:
            logger.error("❌ Нет компонентов для запуска")
            sys.exit(1)
        
        # Обработчик сигналов
        stop_event = asyncio.Event()
        
        def signal_handler(signum, frame):
            logger.info(f"🛑 Получен сигнал {signum}, останавливаем систему...")
            stop_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("✅ Все компоненты запущены!")
        logger.info("📝 Для остановки нажмите Ctrl+C")
        logger.info("🌐 API доступен на: http://localhost:8000")
        logger.info("📊 API документация: http://localhost:8000/docs")
        
        # Ожидание сигнала остановки
        await stop_event.wait()
        
        # Graceful shutdown
        logger.info("🔄 Останавливаем компоненты...")
        
        for name, task in tasks:
            logger.info(f"  🛑 Останавливаем {name}...")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ Все компоненты остановлены")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def run_api_server():
    """Запуск API сервера"""
    import uvicorn
    from api.main import app
    
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
    
    server = uvicorn.Server(config)
    await server.serve()


async def run_telegram_bot_wrapper():
    """Обертка для запуска Telegram бота с обработкой ошибок"""
    logger = logging.getLogger(__name__)
    try:
        await run_telegram_bot()
    except Exception as e:
        logger.error(f"❌ Telegram бот завершился с ошибкой: {e}")
        # Не прерываем работу всей системы


async def run_telegram_bot():
    """Запуск Telegram бота через API"""
    from tools.modern_telegram_bot import ModernTelegramBot
    from tools.telegram_api_client import create_api_callback
    
    logger = logging.getLogger(__name__)
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не настроен")
        return
    
    try:
        # Создаем callback через API
        api_callback, api_client = create_api_callback("http://localhost:8000")
        
        # Создаем бота
        bot = ModernTelegramBot(
            token=token,
            mas_callback=api_callback,
            enable_voice=False
        )
        
        # Запускаем бота
        await bot.run()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска Telegram бота: {e}")
        # Не прерываем работу всей системы из-за ошибки бота
        logger.warning("⚠️ Система продолжит работу без Telegram бота")
    finally:
        if 'api_client' in locals():
            await api_client.stop()


def print_banner():
    """Печатаем красивый баннер"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                          Root-MAS                            ║
    ║                   Multi-Agent System                         ║
    ║                                                              ║
    ║  🤖 Агенты      📱 Telegram     🌐 API      📊 Метрики      ║
    ║  💬 Чат         🔍 Поиск        📋 Задачи   📈 Аналитика   ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


if __name__ == "__main__":
    print_banner()
    
    # Проверяем Python версию
    if sys.version_info < (3, 9):
        print("❌ Требуется Python 3.9 или выше")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)