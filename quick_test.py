#!/usr/bin/env python3
"""
Быстрый тест работоспособности Root-MAS System
Проверяет все критические компоненты
"""

import sys
import os
from pathlib import Path

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_status(status, message):
    """Красивый вывод статуса"""
    if status == "ok":
        print(f"{GREEN}✅{RESET} {message}")
    elif status == "error":
        print(f"{RED}❌{RESET} {message}")
    elif status == "warning":
        print(f"{YELLOW}⚠️{RESET} {message}")
    elif status == "info":
        print(f"{BLUE}ℹ️{RESET} {message}")

def check_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    if version < (3, 9):
        print_status("error", f"Python {version.major}.{version.minor} - требуется 3.9+")
        return False
    elif version >= (3, 14):
        print_status("error", f"Python {version.major}.{version.minor} - AutoGen не поддерживает 3.14+")
        return False
    else:
        print_status("ok", f"Python {version.major}.{version.minor}.{version.micro}")
        return True

def check_env_file():
    """Проверка наличия .env файла"""
    env_path = Path(".env")
    env_example = Path(".env.example")
    
    if env_path.exists():
        print_status("ok", ".env файл найден")
        # Проверяем ключи
        with open(env_path, 'r') as f:
            content = f.read()
            if "your-openrouter-api-key-here" in content or "OPENROUTER_API_KEY=" not in content:
                print_status("warning", "OPENROUTER_API_KEY не настроен в .env")
                return False
        return True
    elif env_example.exists():
        print_status("warning", ".env не найден, но есть .env.example")
        print_status("info", "Скопируйте: cp .env.example .env")
        return False
    else:
        print_status("error", "Нет .env и .env.example файлов")
        return False

def check_imports():
    """Проверка критических импортов"""
    imports_ok = True
    
    # Проверяем AutoGen
    try:
        import autogen_agentchat
        import autogen_ext
        import autogen_core
        print_status("ok", "AutoGen v0.4+ установлен")
    except ImportError as e:
        print_status("error", f"AutoGen не установлен: {e}")
        print_status("info", "Запустите: pip install autogen-agentchat>=0.5.1 autogen-ext[openai]>=0.5.5")
        imports_ok = False
    
    # Проверяем другие важные пакеты
    critical_packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("aiohttp", "aiohttp"),
        ("redis", "Redis client"),
        ("chromadb", "ChromaDB"),
    ]
    
    for package, name in critical_packages:
        try:
            __import__(package)
            print_status("ok", f"{name} установлен")
        except ImportError:
            print_status("warning", f"{name} не установлен")
            imports_ok = False
    
    return imports_ok

def check_project_structure():
    """Проверка структуры проекта"""
    required_dirs = ["agents", "config", "prompts", "tools", "api"]
    required_files = ["run_system.py", "requirements.txt"]
    
    all_ok = True
    
    for dir_name in required_dirs:
        if Path(dir_name).is_dir():
            print_status("ok", f"Директория {dir_name}/ найдена")
        else:
            print_status("error", f"Директория {dir_name}/ отсутствует")
            all_ok = False
    
    for file_name in required_files:
        if Path(file_name).is_file():
            print_status("ok", f"Файл {file_name} найден")
        else:
            print_status("error", f"Файл {file_name} отсутствует")
            all_ok = False
    
    return all_ok

def check_agents():
    """Проверка создания агентов"""
    try:
        from agents.base import BaseAgent
        agent = BaseAgent("test", model="gpt-3.5-turbo", tier="cheap")
        print_status("ok", "Базовый агент создается")
        return True
    except Exception as e:
        print_status("error", f"Ошибка создания агента: {e}")
        return False

def main():
    """Главная функция теста"""
    print(f"\n{BLUE}🔍 Root-MAS System Quick Test{RESET}\n")
    
    results = []
    
    # 1. Python версия
    print(f"{BLUE}1. Проверка Python:{RESET}")
    results.append(check_python_version())
    
    # 2. Файл конфигурации
    print(f"\n{BLUE}2. Проверка конфигурации:{RESET}")
    results.append(check_env_file())
    
    # 3. Импорты
    print(f"\n{BLUE}3. Проверка зависимостей:{RESET}")
    results.append(check_imports())
    
    # 4. Структура проекта
    print(f"\n{BLUE}4. Проверка структуры проекта:{RESET}")
    results.append(check_project_structure())
    
    # 5. Агенты
    print(f"\n{BLUE}5. Проверка агентов:{RESET}")
    results.append(check_agents())
    
    # Итоги
    print(f"\n{BLUE}═══ ИТОГИ ═══{RESET}")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print_status("ok", f"Все проверки пройдены ({passed}/{total})")
        print(f"\n{GREEN}🎉 Система готова к запуску!{RESET}")
        print(f"\nЗапустите: {BLUE}python run_system.py{RESET}")
    else:
        print_status("error", f"Пройдено проверок: {passed}/{total}")
        print(f"\n{YELLOW}⚠️  Исправьте проблемы выше перед запуском{RESET}")
        
        if not results[2]:  # Если не установлены зависимости
            print(f"\n{BLUE}Рекомендуется запустить:{RESET}")
            print("  python install_and_run.py")
        
        sys.exit(1)

if __name__ == "__main__":
    main()