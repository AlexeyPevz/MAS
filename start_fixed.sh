#!/bin/bash
# Скрипт для запуска исправленной версии Root-MAS

echo "🚀 Starting Fixed Root-MAS API..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found!"
    exit 1
fi

# Устанавливаем переменные окружения
export OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-"test-key"}
export REDIS_HOST=${REDIS_HOST:-"localhost"}
export TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-"test-token"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

# Проверяем зависимости
echo "📦 Checking dependencies..."
python3 -c "import fastapi, pydantic, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ Missing dependencies. Installing..."
    pip3 install --break-system-packages fastapi uvicorn pydantic
fi

# Выбираем режим запуска
MODE=${1:-"fixed"}

case $MODE in
    "fixed")
        echo "🔧 Running fixed version..."
        python3 fixed_main.py
        ;;
    
    "safe")
        echo "🛡️ Running safe mode..."
        python3 safe_start.py
        ;;
    
    "diagnose")
        echo "🔍 Running diagnostics..."
        python3 diagnose.py
        ;;
    
    "original")
        echo "⚠️ Running original version (may hang)..."
        python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
        ;;
    
    *)
        echo "Usage: $0 [fixed|safe|diagnose|original]"
        echo "  fixed    - Run fixed API server (recommended)"
        echo "  safe     - Run minimal safe mode"
        echo "  diagnose - Run system diagnostics"
        echo "  original - Run original version (dangerous)"
        exit 1
        ;;
esac