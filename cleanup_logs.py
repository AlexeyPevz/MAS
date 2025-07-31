#!/usr/bin/env python3
"""
Экстренная очистка логов
Использовать когда логи забили весь диск
"""

import os
import shutil
import glob
from pathlib import Path


def emergency_cleanup():
    """Экстренная очистка всех логов"""
    print("🚨 ЭКСТРЕННАЯ ОЧИСТКА ЛОГОВ")
    print("=" * 40)
    
    # Директории с логами
    log_dirs = [
        "logs",
        "/var/log",
        "/tmp", 
        ".",  # Текущая директория
    ]
    
    # Паттерны файлов логов
    log_patterns = [
        "*.log",
        "*.log.*",
        "*.out",
        "*.err",
        "system.log*",
        "autogen*.log",
        "telegram*.log",
        "api*.log",
        "debug*.log",
        "error*.log"
    ]
    
    total_removed = 0
    total_size = 0
    
    for log_dir in log_dirs:
        if not os.path.exists(log_dir):
            continue
            
        print(f"\n📁 Проверяем {log_dir}...")
        
        for pattern in log_patterns:
            for file_path in glob.glob(os.path.join(log_dir, pattern)):
                try:
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        total_removed += 1
                        total_size += file_size
                        print(f"  🗑️ Удален: {file_path} ({file_size//1024//1024}MB)")
                except Exception as e:
                    print(f"  ❌ Ошибка {file_path}: {e}")
    
    print(f"\n✅ Очистка завершена:")
    print(f"📁 Удалено файлов: {total_removed}")
    print(f"💾 Освобождено места: {total_size//1024//1024}MB")
    
    return total_removed, total_size


def check_disk_space():
    """Проверка свободного места на диске"""
    try:
        statvfs = os.statvfs('.')
        free_space = statvfs.f_frsize * statvfs.f_bavail
        total_space = statvfs.f_frsize * statvfs.f_blocks
        used_space = total_space - free_space
        
        free_gb = free_space // 1024 // 1024 // 1024
        used_gb = used_space // 1024 // 1024 // 1024
        total_gb = total_space // 1024 // 1024 // 1024
        
        usage_percent = (used_space / total_space) * 100
        
        print(f"💾 Диск: {used_gb}GB / {total_gb}GB ({usage_percent:.1f}%)")
        print(f"🆓 Свободно: {free_gb}GB")
        
        if usage_percent > 90:
            print("🚨 КРИТИЧНО: Диск заполнен больше чем на 90%!")
            return True
        elif usage_percent > 80:
            print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Диск заполнен больше чем на 80%")
            return False
        else:
            print("✅ Места на диске достаточно")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки диска: {e}")
        return False


def find_large_log_files(min_size_mb: int = 100):
    """Поиск больших файлов логов"""
    print(f"\n🔍 Поиск файлов логов больше {min_size_mb}MB...")
    
    large_files = []
    
    for root, dirs, files in os.walk("."):
        # Пропускаем системные директории
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        for file in files:
            if any(pattern in file.lower() for pattern in ['log', 'out', 'err']):
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    size_mb = size // 1024 // 1024
                    
                    if size_mb >= min_size_mb:
                        large_files.append((file_path, size_mb))
                        print(f"  📁 {file_path}: {size_mb}MB")
                        
                except Exception:
                    pass
    
    if large_files:
        print(f"\n🎯 Найдено {len(large_files)} больших файлов логов")
        total_size = sum(size for _, size in large_files)
        print(f"📊 Общий размер: {total_size}MB")
        
        answer = input("\n❓ Удалить все большие файлы логов? (y/N): ").strip().lower()
        if answer == 'y':
            for file_path, size_mb in large_files:
                try:
                    os.remove(file_path)
                    print(f"  🗑️ Удален: {file_path}")
                except Exception as e:
                    print(f"  ❌ Ошибка: {e}")
    else:
        print("✅ Больших файлов логов не найдено")


def setup_log_rotation():
    """Настройка ротации логов через logrotate"""
    logrotate_config = """
# Root-MAS Log Rotation
/workspace/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    copytruncate
    maxsize 50M
}
"""
    
    try:
        with open("/etc/logrotate.d/rootmas", "w") as f:
            f.write(logrotate_config)
        print("✅ Настроена автоматическая ротация логов")
    except PermissionError:
        print("⚠️ Нет прав для настройки logrotate")
        print("Выполните как root:")
        print(f"echo '{logrotate_config}' > /etc/logrotate.d/rootmas")


def main():
    """Главная функция"""
    print("🧹 УТИЛИТА ОЧИСТКИ ЛОГОВ Root-MAS")
    print("=" * 50)
    
    # Проверяем состояние диска
    critical = check_disk_space()
    
    if critical:
        print("\n🚨 КРИТИЧЕСКОЕ СОСТОЯНИЕ ДИСКА!")
        answer = input("❓ Выполнить экстренную очистку всех логов? (y/N): ").strip().lower()
        if answer == 'y':
            emergency_cleanup()
    else:
        # Ищем большие файлы
        find_large_log_files(min_size_mb=50)
    
    # Настройка ротации
    print(f"\n🔧 Настройка автоматической ротации...")
    setup_log_rotation()
    
    print(f"\n✅ Готово! Для предотвращения проблем в будущем:")
    print(f"1. Используйте ENVIRONMENT=production для минимума логов")
    print(f"2. Регулярно запускайте: python cleanup_logs.py")
    print(f"3. Мониторьте место на диске")


if __name__ == "__main__":
    main()