#!/bin/bash
# Root-MAS Quick Start Script
# Быстрый запуск системы с автоматической установкой зависимостей

echo "🚀 Root-MAS Quick Start"
echo "======================"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден! Установите Python 3.8+"
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Создаю виртуальное окружение..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Активирую виртуальное окружение..."
source venv/bin/activate || . venv/Scripts/activate

# Upgrade pip
echo "📦 Обновляю pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Устанавливаю зависимости..."
pip install -r requirements.txt

# Create missing directories
echo "📁 Создаю необходимые директории..."
mkdir -p data/{metrics,learning,events,knowledge_graph,federation,ab_tests}
mkdir -p logs
mkdir -p workspace

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo "📝 Создаю .env файл..."
    cp .env.example .env
    echo ""
    echo "⚠️  ВНИМАНИЕ: Отредактируйте .env файл и добавьте:"
    echo "   - OPENAI_API_KEY"
    echo "   - TELEGRAM_BOT_TOKEN (если используете Telegram)"
    echo ""
fi

# Create missing routing.yaml
if [ ! -f "config/routing.yaml" ]; then
    echo "📝 Создаю routing.yaml..."
    cat > config/routing.yaml << 'EOF'
# Agent routing configuration
routing:
  meta:
    - coordination
  
  coordination:
    - researcher
    - multi_tool
    - workflow_builder
    - webapp_builder
    - prompt_builder
    - model_selector
    - budget_manager
    - communicator
  
  researcher:
    - fact_checker
  
  workflow_builder:
    - multi_tool
  
  webapp_builder:
    - multi_tool
EOF
fi

# Run system check
echo ""
echo "🔍 Проверяю систему..."
python3 check_system.py

# Check if system is ready
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Система готова к запуску!"
    echo ""
    echo "Доступные команды:"
    echo "  ./quickstart.sh api      # Запустить API сервер"
    echo "  ./quickstart.sh telegram # Запустить Telegram бота"
    echo "  ./quickstart.sh all      # Запустить всё"
    echo "  ./quickstart.sh test     # Тестовый запуск"
    
    # Handle command line arguments
    case "$1" in
        api)
            echo ""
            echo "🌐 Запускаю API сервер..."
            python3 api/main.py
            ;;
        telegram)
            echo ""
            echo "🤖 Запускаю Telegram бота..."
            python3 tools/modern_telegram_bot.py
            ;;
        all)
            echo ""
            echo "🚀 Запускаю полную систему..."
            python3 run_system.py
            ;;
        test)
            echo ""
            echo "🧪 Тестовый запуск..."
            python3 -c "
from tools.smart_groupchat import SmartGroupChatManager
import asyncio

async def test():
    chat = SmartGroupChatManager()
    response = await chat.process_message('Привет! Как дела?')
    print(f'Ответ: {response}')

asyncio.run(test())
"
            ;;
        *)
            echo ""
            echo "💡 Подсказка: используйте './quickstart.sh api' для запуска API"
            ;;
    esac
else
    echo ""
    echo "❌ Система не готова. Проверьте ошибки выше."
    echo ""
    echo "Обычные проблемы:"
    echo "1. Отсутствует OPENAI_API_KEY в .env"
    echo "2. Не установлены системные зависимости (Redis, PostgreSQL)"
    echo "3. Ошибки в коде модулей"
fi