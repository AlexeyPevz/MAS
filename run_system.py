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

# Импортируем централизованные настройки
from config.settings import validate_required_settings, ENVIRONMENT, API_HOST, API_PORT


def cleanup_old_processes():
    """Очистка старых процессов перед запуском"""
    import subprocess
    try:
        import psutil
    except ImportError:
        psutil = None
    
    logger = logging.getLogger(__name__)
    
    if psutil:
        try:
            # Получаем текущий PID
            current_pid = os.getpid()
            
            # Сначала пытаемся очистить зомби-процессы
            for proc in psutil.process_iter(['pid', 'ppid', 'name', 'status']):
                try:
                    if proc.info['status'] == psutil.STATUS_ZOMBIE:
                        logger.info(f"🧟 Обнаружен зомби-процесс PID: {proc.info['pid']}")
                        # Зомби нельзя убить напрямую, но можно попытаться очистить через wait
                        try:
                            os.waitpid(proc.info['pid'], os.WNOHANG)
                        except:
                            pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Теперь ищем и останавливаем старые процессы Python с run_system.py
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] != current_pid and proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and any('run_system.py' in arg for arg in cmdline):
                            logger.info(f"🧹 Останавливаем старый процесс PID: {proc.info['pid']}")
                            proc.terminate()
                            try:
                                proc.wait(timeout=3)
                            except psutil.TimeoutExpired:
                                proc.kill()
                                proc.wait(timeout=1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
        except Exception as e:
            logger.error(f"Ошибка при очистке процессов: {e}")
    else:
        # Fallback если psutil не установлен
        logger.warning("⚠️ psutil не установлен, используем pkill")
        subprocess.run(['pkill', '-f', 'python.*run_system.py', '-F', str(os.getpid())], 
                      capture_output=True, text=True)


async def main():
    """Главная функция запуска системы"""
    
    # Настраиваем обработчик SIGCHLD для предотвращения зомби
    def handle_sigchld(signum, frame):
        try:
            while True:
                # Очищаем завершившиеся дочерние процессы
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
        except OSError:
            pass
    
    signal.signal(signal.SIGCHLD, handle_sigchld)
    
    # Очищаем старые процессы
    cleanup_old_processes()
    
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
        
        # Проверяем обязательные настройки
        errors = validate_required_settings()
        if errors:
            for error in errors:
                logger.error(f"❌ {error}")
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
        api_port = int(os.getenv("API_PORT", "8000"))
        logger.info(f"🌐 API доступен на: http://localhost:{api_port}")
        logger.info(f"📊 API документация: http://localhost:{api_port}/docs")
        
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
        host=API_HOST,
        port=API_PORT,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
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
    """Запуск Telegram бота через API с поддержкой streaming"""
    from tools.telegram_api_client import create_api_callback
    
    logger = logging.getLogger(__name__)
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не настроен")
        return
    
    # Проверяем, включен ли streaming
    enable_streaming = os.getenv("TELEGRAM_STREAMING", "true").lower() == "true"
    
    try:
        # Создаем callback через API
        api_port = int(os.getenv("API_PORT", "8000"))
        api_callback, api_client = create_api_callback(f"http://localhost:{api_port}")
        
        if enable_streaming:
            # Используем streaming версию бота
            from tools.streaming_telegram_bot import StreamingTelegramBot, create_streaming_callback
            logger.info("🌊 Включен режим streaming для Telegram бота")
            
            # Создаем streaming callback
            # В будущем здесь будет использоваться streaming из SmartGroupChatManager
            async def streaming_callback(message: str, user_id: str):
                """Временный streaming callback через API"""
                # Пока используем обычный ответ, разбитый на части
                response = await api_callback(message)
                
                # Имитируем streaming
                words = response.split()
                chunk = ""
                for i, word in enumerate(words):
                    chunk += word + " "
                    if (i + 1) % 3 == 0 or i == len(words) - 1:
                        yield chunk
                        chunk = ""
                        await asyncio.sleep(0.05)
            
            bot = StreamingTelegramBot(
                token=token,
                mas_callback=api_callback,
                streaming_callback=streaming_callback,
                streaming_delay=0.3,
                enable_voice=False
            )
        else:
            # Используем обычную версию
            from tools.modern_telegram_bot import ModernTelegramBot
            logger.info("📱 Используется обычный режим Telegram бота")
            
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
    
    if sys.version_info >= (3, 13):
        print("⚠️  ВНИМАНИЕ: Python 3.13+ имеет проблемы совместимости с некоторыми зависимостями!")
        print("⚠️  Рекомендуется использовать Python 3.10 - 3.11")
        print("⚠️  Известные проблемы:")
        print("   - python-telegram-bot не совместим с 3.13")
        print("   - Некоторые пакеты autogen могут работать нестабильно")
        print()
        response = input("Продолжить на свой риск? (y/N): ")
        if response.lower() != 'y':
            print("👋 Установка отменена. Рекомендуем использовать Python 3.11")
            sys.exit(0)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)