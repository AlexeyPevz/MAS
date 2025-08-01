#!/usr/bin/env python3
"""
Автоматическая установка зависимостей и запуск Root-MAS System
Проверяет и устанавливает все необходимые пакеты перед запуском
"""

import os
import sys
import subprocess
import pkg_resources
from pathlib import Path


def print_banner():
    """Печатаем красивый баннер"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║              Root-MAS Auto-Installer & Launcher              ║
    ║                                                              ║
    ║  Автоматическая установка зависимостей и запуск системы     ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_python_version():
    """Проверка версии Python"""
    print("🐍 Проверка версии Python...")
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    if version_info < (3, 9):
        print(f"❌ Требуется Python 3.9 или выше, у вас {version_str}")
        sys.exit(1)
    elif version_info >= (3, 14):
        print(f"❌ AutoGen не поддерживает Python 3.14+, у вас {version_str}")
        print("   Установите Python 3.9-3.13")
        sys.exit(1)
    elif version_info.major == 3 and version_info.minor == 13:
        print(f"⚠️  Python {version_str} - экспериментальная поддержка в AutoGen")
        print("   Рекомендуется Python 3.9-3.12 для стабильной работы")
    else:
        print(f"✅ Python {version_str} - OK")


def get_installed_version(package_name):
    """Получить установленную версию пакета"""
    try:
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        return None


def check_and_install_packages():
    """Проверка и установка необходимых пакетов"""
    print("\n📦 Проверка и установка зависимостей...")
    
    # Критически важные пакеты для новой версии AutoGen
    critical_packages = {
        "autogen-agentchat": ">=0.5.1",
        "autogen-ext": ">=0.5.5",
        "autogen-core": None,  # Будет установлен как зависимость
    }
    
    # Проверяем установлен ли старый pyautogen
    old_autogen = get_installed_version("pyautogen")
    if old_autogen:
        print(f"⚠️  Обнаружен старый pyautogen {old_autogen}")
        print("🔄 Удаляем старую версию...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "pyautogen"])
            print("✅ Старая версия удалена")
        except subprocess.CalledProcessError:
            print("❌ Не удалось удалить старую версию, продолжаем...")
    
    # Устанавливаем критические пакеты
    packages_to_install = []
    
    for package, min_version in critical_packages.items():
        current_version = get_installed_version(package)
        
        if current_version is None:
            print(f"❌ {package} не установлен")
            if package == "autogen-ext":
                packages_to_install.append("autogen-ext[openai]>=0.5.5")
            else:
                packages_to_install.append(package + (min_version or ""))
        elif min_version and not pkg_resources.parse_version(current_version) >= pkg_resources.parse_version(min_version.strip(">=")):
            print(f"⚠️  {package} {current_version} устарел (нужен {min_version})")
            if package == "autogen-ext":
                packages_to_install.append("autogen-ext[openai]>=0.5.5")
            else:
                packages_to_install.append(package + min_version)
        else:
            print(f"✅ {package} {current_version} - OK")
    
    # Устанавливаем недостающие пакеты
    if packages_to_install:
        print(f"\n📥 Устанавливаем: {', '.join(packages_to_install)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages_to_install)
            print("✅ Критические пакеты установлены")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки пакетов: {e}")
            sys.exit(1)
    
    # Устанавливаем остальные зависимости из requirements.txt
    print("\n📋 Установка остальных зависимостей из requirements.txt...")
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if requirements_file.exists():
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
            print("✅ Все зависимости установлены")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки зависимостей: {e}")
            sys.exit(1)
    else:
        print("⚠️  requirements.txt не найден")


def verify_autogen_installation():
    """Проверка корректности установки AutoGen"""
    print("\n🔍 Проверка установки AutoGen...")
    
    try:
        # Проверяем импорты
        import autogen_agentchat
        print("✅ autogen_agentchat импортирован")
        
        import autogen_ext
        print("✅ autogen_ext импортирован")
        
        import autogen_core
        print("✅ autogen_core импортирован")
        
        # Проверяем основные классы
        from autogen_agentchat.agents import AssistantAgent
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        from autogen_core import CancellationToken
        print("✅ Основные классы доступны")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта AutoGen: {e}")
        return False


def check_environment_variables():
    """Проверка переменных окружения"""
    print("\n🔑 Проверка переменных окружения...")
    
    required_vars = {
        "OPENROUTER_API_KEY": "API ключ для OpenRouter (LLM модели)",
    }
    
    optional_vars = {
        "TELEGRAM_BOT_TOKEN": "Токен для Telegram бота",
        "YANDEX_API_KEY": "API ключ для Yandex SpeechKit",
    }
    
    missing_required = []
    
    # Проверяем обязательные переменные
    for var, description in required_vars.items():
        if os.getenv(var):
            print(f"✅ {var} - установлен")
        else:
            print(f"❌ {var} - не установлен ({description})")
            missing_required.append(var)
    
    # Проверяем опциональные переменные
    for var, description in optional_vars.items():
        if os.getenv(var):
            print(f"✅ {var} - установлен")
        else:
            print(f"⚠️  {var} - не установлен ({description})")
    
    if missing_required:
        print(f"\n❌ Отсутствуют обязательные переменные: {', '.join(missing_required)}")
        print("\n💡 Установите переменные окружения:")
        print("   Linux/Mac: export OPENROUTER_API_KEY='your-key-here'")
        print("   Windows:   set OPENROUTER_API_KEY=your-key-here")
        print("\n   Или создайте файл .env в корне проекта")
        return False
    
    return True


def create_env_template():
    """Создание шаблона .env файла если его нет"""
    env_file = Path(__file__).parent / ".env"
    env_template = Path(__file__).parent / ".env.template"
    
    if not env_file.exists() and not env_template.exists():
        print("\n📄 Создаю шаблон .env.template...")
        template_content = """# Root-MAS Environment Variables

# ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ
# OpenRouter API key для LLM моделей
OPENROUTER_API_KEY=your-openrouter-api-key-here

# ОПЦИОНАЛЬНЫЕ ПЕРЕМЕННЫЕ
# Telegram Bot Token (если нужен Telegram бот)
# TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here

# Yandex SpeechKit API key (для голосовых функций)
# YANDEX_API_KEY=your-yandex-api-key-here

# Режим запуска: full, api, mas
RUN_MODE=full

# Окружение: production, development
ENVIRONMENT=production
"""
        with open(env_template, "w", encoding="utf-8") as f:
            f.write(template_content)
        print(f"✅ Создан {env_template}")
        print("   Скопируйте его в .env и заполните ваши API ключи")


def run_quick_test():
    """Быстрый тест работоспособности"""
    print("\n🧪 Быстрый тест системы...")
    
    try:
        # Проверяем создание агента
        from agents.base import BaseAgent
        agent = BaseAgent("test", model="gpt-3.5-turbo", tier="cheap")
        print("✅ Тестовый агент создан")
        
        # Проверяем SmartGroupChatManager
        from tools.smart_groupchat import SmartGroupChatManager
        manager = SmartGroupChatManager()
        print("✅ SmartGroupChatManager работает")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False


def launch_system():
    """Запуск основной системы"""
    print("\n🚀 Запуск Root-MAS System...")
    
    run_system_path = Path(__file__).parent / "run_system.py"
    
    if not run_system_path.exists():
        print("❌ Файл run_system.py не найден!")
        sys.exit(1)
    
    try:
        # Запускаем основную систему
        subprocess.call([sys.executable, str(run_system_path)])
    except KeyboardInterrupt:
        print("\n👋 Программа прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка запуска системы: {e}")
        sys.exit(1)


def main():
    """Главная функция"""
    print_banner()
    
    # 1. Проверяем Python
    check_python_version()
    
    # 2. Устанавливаем пакеты
    check_and_install_packages()
    
    # 3. Проверяем установку AutoGen
    if not verify_autogen_installation():
        print("\n❌ AutoGen установлен некорректно. Попробуйте:")
        print("   1. Удалить виртуальное окружение и создать заново")
        print("   2. pip install --upgrade pip")
        print("   3. Запустить этот скрипт снова")
        sys.exit(1)
    
    # 4. Создаем шаблон .env если нужно
    create_env_template()
    
    # 5. Проверяем переменные окружения
    if not check_environment_variables():
        print("\n⚠️  Система может работать некорректно без API ключей")
        response = input("\nПродолжить все равно? (y/N): ")
        if response.lower() != 'y':
            print("Запуск отменен")
            sys.exit(0)
    
    # 6. Быстрый тест
    if not run_quick_test():
        print("\n⚠️  Быстрый тест не пройден, но можно попробовать запустить")
        response = input("\nПродолжить? (y/N): ")
        if response.lower() != 'y':
            print("Запуск отменен")
            sys.exit(0)
    
    print("\n✅ Все проверки пройдены!")
    print("=" * 60)
    
    # 7. Запускаем систему
    launch_system()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)