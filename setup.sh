#!/bin/bash
# Setup script for Root-MAS System
# Автоматическая настройка окружения и установка зависимостей

set -e  # Останавливаемся при ошибках

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Root-MAS System Setup Script                    ║"
echo "║                                                              ║"
echo "║  Автоматическая настройка окружения для Linux/Mac           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Функция для проверки команды
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Определяем ОС
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo "❌ Неподдерживаемая ОС: $OSTYPE"
    exit 1
fi

echo "🖥️  Обнаружена ОС: $OS"

# Проверяем Python
echo ""
echo "🐍 Проверка Python..."

PYTHON_CMD=""
PYTHON_VERSION=""

# Проверяем разные варианты Python
for cmd in python3.11 python3.10 python3.9 python3 python; do
    if command_exists $cmd; then
        version=$($cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        major=$(echo $version | cut -d. -f1)
        minor=$(echo $version | cut -d. -f2)
        
        if [ "$major" -eq 3 ] && [ "$minor" -ge 9 ] && [ "$minor" -lt 14 ]; then
            PYTHON_CMD=$cmd
            PYTHON_VERSION=$version
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python 3.9-3.13 не найден!"
    echo ""
    echo "📦 Установка Python 3.11..."
    
    if [ "$OS" == "linux" ]; then
        # Для Ubuntu/Debian
        if command_exists apt-get; then
            sudo apt-get update
            sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
            PYTHON_CMD="python3.11"
        # Для CentOS/RHEL/Fedora
        elif command_exists yum; then
            sudo yum install -y python311 python311-devel
            PYTHON_CMD="python3.11"
        else
            echo "❌ Не могу установить Python автоматически"
            echo "   Установите Python 3.9-3.13 вручную"
            exit 1
        fi
    elif [ "$OS" == "macos" ]; then
        if command_exists brew; then
            brew install python@3.11
            PYTHON_CMD="python3.11"
        else
            echo "❌ Homebrew не установлен"
            echo "   Установите Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo "   Затем запустите: brew install python@3.11"
            exit 1
        fi
    fi
fi

echo "✅ Python найден: $PYTHON_CMD (версия $PYTHON_VERSION)"

# Проверяем pip
echo ""
echo "📦 Проверка pip..."
if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    echo "❌ pip не установлен, устанавливаю..."
    $PYTHON_CMD -m ensurepip --upgrade || {
        echo "❌ Не удалось установить pip"
        exit 1
    }
fi
echo "✅ pip установлен"

# Создаем виртуальное окружение
echo ""
echo "🔧 Настройка виртуального окружения..."
VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    echo "⚠️  Виртуальное окружение уже существует"
    read -p "   Пересоздать? (это удалит текущее окружение) [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        $PYTHON_CMD -m venv "$VENV_DIR"
        echo "✅ Виртуальное окружение пересоздано"
    fi
else
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "✅ Виртуальное окружение создано"
fi

# Активируем виртуальное окружение
source "$VENV_DIR/bin/activate"

# Обновляем pip
echo ""
echo "📦 Обновление pip..."
python -m pip install --upgrade pip setuptools wheel

# Устанавливаем зависимости
echo ""
echo "📦 Установка зависимостей..."

# Сначала устанавливаем критические пакеты AutoGen
echo "📦 Установка AutoGen v0.4+..."
pip install autogen-agentchat>=0.5.1 autogen-ext[openai]>=0.5.5

# Затем остальные зависимости
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt не найден"
fi

# Создаем .env файл если его нет
echo ""
echo "📄 Проверка конфигурации..."
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        cp .env.template .env
        echo "✅ Создан файл .env из шаблона"
        echo "   ⚠️  Не забудьте заполнить API ключи в .env!"
    else
        echo "📄 Создаю шаблон .env..."
        cat > .env << EOF
# Root-MAS Environment Variables

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
EOF
        echo "✅ Создан файл .env"
        echo "   ⚠️  Заполните API ключи в .env!"
    fi
fi

# Создаем скрипты запуска
echo ""
echo "📝 Создание скриптов запуска..."

# Скрипт для активации окружения и запуска
cat > start.sh << 'EOF'
#!/bin/bash
# Быстрый запуск Root-MAS System

# Активируем виртуальное окружение
source venv/bin/activate

# Загружаем переменные окружения
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Запускаем систему
python install_and_run.py
EOF

chmod +x start.sh

# Скрипт для Windows
cat > start.bat << 'EOF'
@echo off
REM Быстрый запуск Root-MAS System для Windows

REM Активируем виртуальное окружение
call venv\Scripts\activate.bat

REM Загружаем переменные окружения из .env
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if not "%%a"=="" if not "%%a"==REM set "%%a=%%b"
)

REM Запускаем систему
python install_and_run.py
EOF

echo "✅ Скрипты запуска созданы"

# Финальная проверка
echo ""
echo "🧪 Проверка установки..."
python -c "
try:
    import autogen_agentchat
    import autogen_ext
    import autogen_core
    print('✅ AutoGen установлен корректно')
except ImportError as e:
    print(f'❌ Ошибка импорта: {e}')
    exit(1)
"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🎉 Установка завершена! 🎉                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Дальнейшие шаги:"
echo ""
echo "1. Отредактируйте файл .env и добавьте ваши API ключи"
echo ""
echo "2. Запустите систему одним из способов:"
echo "   • ./start.sh                    (рекомендуется)"
echo "   • source venv/bin/activate && python run_system.py"
echo "   • python install_and_run.py     (с автопроверкой)"
echo ""
echo "3. Откройте в браузере:"
echo "   • http://localhost:8000         (API)"
echo "   • http://localhost:8000/docs    (Документация)"
echo ""
echo "💡 Подсказка: используйте ./start.sh для быстрого запуска!"