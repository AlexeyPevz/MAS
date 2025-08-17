#!/usr/bin/env python3
"""
Root-MAS System Launcher (Fixed version)
Исправленная версия без циклического перезапуска
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

# Настройка простого логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/system.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Глобальный флаг для предотвращения множественных запусков
_running = False
_shutdown_event = None


async def minimal_test_server():
    """Минимальный тестовый сервер для проверки"""
    logger.info("🌐 Starting minimal test server on port 8000...")
    
    try:
        # Пытаемся импортировать FastAPI
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        import uvicorn
        
        app = FastAPI(title="Root-MAS Test")
        
        @app.get("/")
        async def root():
            return JSONResponse({
                "status": "ok",
                "message": "Root-MAS Test Server is running"
            })
        
        @app.get("/health")
        async def health():
            return JSONResponse({"status": "healthy"})
        
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
    except ImportError as e:
        logger.warning(f"⚠️ FastAPI/Uvicorn not available: {e}")
        logger.info("💤 Running in sleep mode (dependencies missing)")
        
        # Просто ждем сигнала остановки
        while not _shutdown_event.is_set():
            await asyncio.sleep(1)


async def main():
    """Главная функция запуска системы"""
    global _running, _shutdown_event
    
    # Проверяем, не запущена ли уже система
    if _running:
        logger.warning("⚠️ System is already running!")
        return
    
    _running = True
    _shutdown_event = asyncio.Event()
    
    logger.info("🚀 Starting Root-MAS System (Fixed Version)...")
    logger.info(f"📂 Working directory: {os.getcwd()}")
    logger.info(f"🐍 Python version: {sys.version}")
    
    # Проверяем основные настройки
    environment = os.getenv("ENVIRONMENT", "development")
    logger.info(f"🌍 Environment: {environment}")
    
    # Обработчик сигналов
    def signal_handler(signum, frame):
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        _shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Создаем задачи
    tasks = []
    
    try:
        # Запускаем минимальный сервер
        server_task = asyncio.create_task(minimal_test_server())
        tasks.append(("Test Server", server_task))
        
        logger.info("✅ System started successfully!")
        logger.info("📝 Press Ctrl+C to stop")
        
        # Ожидаем сигнала остановки
        await _shutdown_event.wait()
        
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Graceful shutdown
        logger.info("🔄 Shutting down components...")
        
        for name, task in tasks:
            if not task.done():
                logger.info(f"  🛑 Stopping {name}...")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        _running = False
        logger.info("✅ System stopped successfully")


def check_dependencies():
    """Проверка минимальных зависимостей"""
    missing = []
    
    required_modules = [
        ("dotenv", "python-dotenv"),
        ("psutil", "psutil"),
    ]
    
    for module, package in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.warning(f"⚠️ Missing dependencies: {', '.join(missing)}")
        logger.info("Install with: pip3 install " + " ".join(missing))
        return False
    
    return True


def print_banner():
    """Печатаем простой баннер"""
    banner = """
╔════════════════════════════════════════╗
║        Root-MAS (Fixed Version)        ║
║         Multi-Agent System             ║
╚════════════════════════════════════════╝
    """
    print(banner)


if __name__ == "__main__":
    print_banner()
    
    # Проверяем Python версию
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        sys.exit(1)
    
    # Предупреждение для Python 3.13+
    if sys.version_info >= (3, 13):
        print("⚠️  WARNING: Python 3.13+ detected")
        print("   Some dependencies may not be compatible")
        print()
    
    # Проверяем зависимости
    if not check_dependencies():
        print("⚠️  Running with limited functionality")
    
    # Запускаем систему
    try:
        # Используем asyncio.run() только один раз
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Stopped by user")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        sys.exit(1)