"""
Правильная конфигурация логирования с ротацией
Предотвращает переполнение диска логами
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_file_size: int = 50 * 1024 * 1024,  # 50MB
    backup_count: int = 5,  # Держим 5 файлов = максимум 250MB
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Настройка логирования с ротацией файлов
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        log_dir: Директория для логов
        max_file_size: Максимальный размер файла лога в байтах (50MB)
        backup_count: Количество старых файлов для хранения (5 файлов)
        enable_console: Включить вывод в консоль
        enable_file: Включить запись в файл
    """
    
    # Создаем директорию если не существует
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Основной логгер
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Очищаем старые handlers
    logger.handlers.clear()
    
    # Формат логов
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Консольный handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Файловый handler с ротацией
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path / "system.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Ограничиваем болтливые библиотеки
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    
    # Специальные настройки для разных компонентов
    logging.getLogger('autogen').setLevel(logging.WARNING)  # AutoGen очень болтливый
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    logger.info(f"🔧 Логирование настроено: уровень {log_level}, файлы до {max_file_size//1024//1024}MB, {backup_count} бэкапов")
    return logger


def setup_production_logging():
    """Настройки для продакшн среды - минимум логов"""
    return setup_logging(
        log_level="WARNING",  # Только важные сообщения
        max_file_size=10 * 1024 * 1024,  # 10MB на файл
        backup_count=3,  # Максимум 30MB логов
        enable_console=False  # Без консольного вывода
    )


def setup_development_logging():
    """Настройки для разработки - больше деталей"""
    return setup_logging(
        log_level="INFO",
        max_file_size=50 * 1024 * 1024,  # 50MB на файл
        backup_count=5,  # Максимум 250MB логов
        enable_console=True
    )


def cleanup_old_logs(log_dir: str = "logs", days_to_keep: int = 7):
    """Очистка старых логов"""
    import time
    from datetime import datetime, timedelta
    
    log_path = Path(log_dir)
    if not log_path.exists():
        return
    
    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
    removed_count = 0
    removed_size = 0
    
    for log_file in log_path.glob("*.log*"):
        try:
            if log_file.stat().st_mtime < cutoff_time:
                file_size = log_file.stat().st_size
                log_file.unlink()
                removed_count += 1
                removed_size += file_size
        except Exception as e:
            print(f"⚠️ Не удалось удалить {log_file}: {e}")
    
    if removed_count > 0:
        print(f"🧹 Удалено {removed_count} старых логов, освобождено {removed_size//1024//1024}MB")


def get_log_size(log_dir: str = "logs") -> tuple[int, int]:
    """Получение размера логов (файлов, MB)"""
    log_path = Path(log_dir)
    if not log_path.exists():
        return 0, 0
    
    total_size = 0
    file_count = 0
    
    for log_file in log_path.glob("*.log*"):
        try:
            total_size += log_file.stat().st_size
            file_count += 1
        except:
            pass
    
    return file_count, total_size // 1024 // 1024


# Глобальная настройка при импорте
def auto_setup_logging():
    """Автоматическая настройка при импорте"""
    # Проверяем переменную окружения для уровня
    log_level = os.getenv("LOG_LEVEL", "INFO")
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        setup_production_logging()
    else:
        setup_development_logging()


# Функция для мониторинга логов
def log_monitor():
    """Мониторинг размера логов"""
    count, size_mb = get_log_size()
    
    if size_mb > 100:  # Больше 100MB
        print(f"⚠️ ВНИМАНИЕ: Логи занимают {size_mb}MB ({count} файлов)")
        print("🧹 Рекомендуется очистка: python -c 'from tools.logging_config import cleanup_old_logs; cleanup_old_logs()'")
    elif size_mb > 50:
        print(f"📊 Логи: {size_mb}MB ({count} файлов)")
    
    return count, size_mb


if __name__ == "__main__":
    # Тест и мониторинг
    print("🔧 Тестирование логирования...")
    
    logger = setup_development_logging()
    logger.info("Тестовое сообщение INFO")
    logger.warning("Тестовое предупреждение WARNING")
    logger.error("Тестовая ошибка ERROR")
    
    print("\n📊 Текущее состояние логов:")
    count, size_mb = log_monitor()
    
    print(f"📁 Файлов логов: {count}")
    print(f"💾 Размер логов: {size_mb}MB")
    
    if size_mb > 10:
        print("\n🧹 Очистка старых логов...")
        cleanup_old_logs(days_to_keep=3)
        count, size_mb = get_log_size()
        print(f"✅ После очистки: {count} файлов, {size_mb}MB")