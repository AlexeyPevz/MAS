#!/bin/bash

# Скрипт для безопасной остановки Root-MAS системы

echo "🛑 Останавливаем Root-MAS систему..."

# Проверяем lock-файл
if [ -f "run_system.lock" ]; then
    PID=$(cat run_system.lock)
    echo "📍 Найден процесс с PID: $PID"
    
    # Проверяем, существует ли процесс
    if kill -0 $PID 2>/dev/null; then
        echo "🔄 Отправляем сигнал остановки..."
        kill -TERM $PID
        
        # Ждем остановки процесса
        COUNT=0
        while kill -0 $PID 2>/dev/null && [ $COUNT -lt 10 ]; do
            echo -n "."
            sleep 1
            COUNT=$((COUNT+1))
        done
        echo
        
        # Если процесс все еще жив, используем SIGKILL
        if kill -0 $PID 2>/dev/null; then
            echo "⚠️  Процесс не остановился, используем SIGKILL..."
            kill -9 $PID
            sleep 1
        fi
        
        echo "✅ Процесс остановлен"
    else
        echo "⚠️  Процесс $PID не найден"
    fi
    
    # Удаляем lock-файл
    rm -f run_system.lock
    echo "🔓 Lock-файл удален"
else
    echo "ℹ️  Lock-файл не найден, система не запущена"
fi

# Дополнительно проверяем процессы Python
echo "🔍 Проверяем оставшиеся процессы..."
PIDS=$(pgrep -f "python.*run_system.py")
if [ ! -z "$PIDS" ]; then
    echo "⚠️  Найдены процессы: $PIDS"
    echo "   Используйте 'pkill -f run_system.py' для принудительной остановки"
else
    echo "✅ Процессы Python не найдены"
fi

# Проверяем systemd сервис
if systemctl is-active mas-system.service &>/dev/null; then
    echo "🔧 Останавливаем systemd сервис..."
    sudo systemctl stop mas-system.service
fi

echo "✅ Остановка завершена"