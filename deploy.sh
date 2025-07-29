#!/bin/bash

# =================================================================
# MAS System Deployment Script
# Единый скрипт для развертывания всей системы одной командой
# =================================================================

set -e  # Выход при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для красивого вывода
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Функция проверки команд
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 не установлен. Установите его и попробуйте снова."
        exit 1
    fi
}

# Функция создания директорий
create_directories() {
    log_info "Создание необходимых директорий..."
    
    directories=(
        "logs"
        "data"
        "backups"
        "temp"
        "data/postgres"
        "data/redis"
        "data/chroma"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_success "Создана директория: $dir"
    done
}

# Функция проверки переменных окружения
check_environment() {
    log_info "Проверка переменных окружения..."
    
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            log_warning ".env файл не найден. Копирую из .env.example"
            cp .env.example .env
            log_error "Пожалуйста, отредактируйте .env файл и добавьте ваши API ключи"
            log_info "Как минимум требуется: OPENROUTER_API_KEY"
            exit 1
        else
            log_error ".env файл не найден и .env.example отсутствует"
            exit 1
        fi
    fi
    
    # Загружаем переменные окружения
    source .env
    
    # Проверяем обязательные переменные
    if [[ -z "$OPENROUTER_API_KEY" || "$OPENROUTER_API_KEY" == "your_openrouter_api_key_here" ]]; then
        log_error "OPENROUTER_API_KEY не настроен в .env файле"
        exit 1
    fi
    
    log_success "Переменные окружения настроены"
}

# Функция установки Python зависимостей
install_python_deps() {
    log_info "Установка Python зависимостей..."
    
    # Проверяем Python
    check_command python3
    
    # Устанавливаем pip если нужно
    if ! command -v pip3 &> /dev/null; then
        log_warning "pip3 не найден, пытаемся установить..."
        python3 -m ensurepip --upgrade
    fi
    
    # Устанавливаем основные зависимости
    log_info "Установка основных пакетов..."
    pip3 install --break-system-packages -r requirements.txt
    
    # Устанавливаем дополнительные зависимости для production
    log_info "Установка дополнительных пакетов..."
    pip3 install --break-system-packages \
        python-dotenv \
        pyyaml \
        aiofiles \
        uvloop \
        prometheus_client \
        pytest
    
    # Исправляем AutoGen зависимости
    log_info "Настройка AutoGen..."
    pip3 uninstall --break-system-packages -y autogen autogen-agentchat || true
    pip3 install --break-system-packages pyautogen>=0.2.32
    
    # Устанавливаем современный Telegram bot
    log_info "Установка Telegram bot..."
    pip3 install --break-system-packages "python-telegram-bot>=20.0,<21.0"
    
    log_success "Python зависимости установлены"
}

# Функция запуска Docker сервисов
start_docker_services() {
    log_info "Запуск Docker сервисов..."
    
    # Проверяем Docker
    check_command docker
    check_command docker-compose
    
    # Останавливаем существующие контейнеры
    log_info "Остановка существующих контейнеров..."
    docker-compose -f docker-compose.prod.yml down --remove-orphans || true
    
    # Запускаем сервисы
    log_info "Запуск PostgreSQL, Redis, ChromaDB и Prometheus..."
    docker-compose -f docker-compose.prod.yml up -d postgres redis prometheus
    
    # Ждем запуска сервисов
    log_info "Ожидание запуска сервисов..."
    sleep 10
    
    # Проверяем статус
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_success "Docker сервисы запущены"
    else
        log_error "Ошибка запуска Docker сервисов"
        docker-compose -f docker-compose.prod.yml logs
        exit 1
    fi
}

# Функция инициализации базы данных
init_database() {
    log_info "Инициализация базы данных..."
    
    # Ждем готовности PostgreSQL
    log_info "Ожидание готовности PostgreSQL..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U ${POSTGRES_USER:-mas} &> /dev/null; then
            log_success "PostgreSQL готов"
            break
        fi
        
        log_info "Попытка $attempt/$max_attempts - ожидание PostgreSQL..."
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "PostgreSQL не запустился в течение времени ожидания"
        exit 1
    fi
    
    # Запускаем инициализацию
    if [[ -f "examples/init_db.py" ]]; then
        log_info "Запуск инициализации базы данных..."
        python3 examples/init_db.py || log_warning "Инициализация БД завершилась с предупреждениями"
    else
        log_warning "Скрипт инициализации БД не найден"
    fi
}

# Функция тестирования системы
test_system() {
    log_info "Тестирование системы..."
    
    # Тест конфигурации LLM
    log_info "Тестирование LLM конфигурации..."
    python3 tools/llm_config.py
    
    # Тест создания агентов
    log_info "Тестирование создания агентов..."
    python3 -c "
from pathlib import Path
from agents.core_agents import create_agents
from config_loader import AgentsConfig

config = AgentsConfig.from_yaml(Path('config/agents.yaml'))
agents = create_agents(config)
print(f'✅ Создано {len(agents)} агентов из {len(config.agents)} в конфигурации')

missing = set(config.agents.keys()) - set(agents.keys())
if missing:
    print(f'❌ Отсутствуют: {missing}')
    exit(1)
else:
    print('🎉 Все агенты созданы успешно!')
"
    
    if [[ $? -eq 0 ]]; then
        log_success "Тесты пройдены"
    else
        log_error "Тесты провалились"
        exit 1
    fi
}

# Функция запуска MAS системы
start_mas_system() {
    log_info "Запуск MAS системы..."
    
    # Создаем systemd сервис (опционально)
    create_systemd_service
    
    # Запускаем систему
    log_info "Запуск production launcher..."
    log_info "Система будет доступна в интерактивном режиме"
    log_info "Для завершения используйте Ctrl+C"
    
    python3 production_launcher.py
}

# Функция создания systemd сервиса
create_systemd_service() {
    if [[ "$EUID" -eq 0 ]] && command -v systemctl &> /dev/null; then
        log_info "Создание systemd сервиса..."
        
        cat > /etc/systemd/system/mas-system.service << EOF
[Unit]
Description=Multi-Agent System (MAS)
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=$(which python3) production_launcher.py
ExecStop=/bin/kill -TERM \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        systemctl daemon-reload
        systemctl enable mas-system.service
        
        log_success "Systemd сервис создан. Используйте: systemctl start mas-system"
    else
        log_info "Systemd сервис не создан (требуются root права или systemd недоступен)"
    fi
}

# Функция показа статуса
show_status() {
    log_info "Статус системы:"
    echo
    
    # Docker сервисы
    log_info "Docker сервисы:"
    docker-compose -f docker-compose.prod.yml ps
    echo
    
    # Порты
    log_info "Доступные порты:"
    echo "  • PostgreSQL: ${POSTGRES_PORT:-5432}"
    echo "  • Redis: ${REDIS_PORT:-6379}"
    echo "  • ChromaDB: ${CHROMA_PORT:-8000}"
    echo "  • Prometheus: ${PROMETHEUS_PORT:-9000}"
    echo "  • MAS API: 8000 (в будущей версии)"
    echo
    
    # API ключи
    log_info "API ключи:"
    python3 -c "
from tools.llm_config import validate_api_keys
api_status = validate_api_keys()
for provider, available in api_status.items():
    status = '✅' if available else '❌'
    print(f'  {status} {provider}')
"
}

# Функция полной остановки
stop_system() {
    log_info "Остановка MAS системы..."
    
    # Останавливаем Docker сервисы
    docker-compose -f docker-compose.prod.yml down
    
    # Останавливаем systemd сервис если есть
    if systemctl is-active mas-system.service &> /dev/null; then
        systemctl stop mas-system.service
    fi
    
    log_success "Система остановлена"
}

# Функция очистки
cleanup() {
    log_info "Очистка системы..."
    
    # Останавливаем все
    stop_system
    
    # Удаляем временные файлы
    rm -rf temp/*
    
    # Очищаем Docker
    docker system prune -f
    
    log_success "Очистка завершена"
}

# Функция помощи
show_help() {
    echo "MAS System Deployment Script"
    echo
    echo "Использование:"
    echo "  $0 [команда]"
    echo
    echo "Команды:"
    echo "  install     - Установка зависимостей и настройка"
    echo "  start       - Запуск всей системы"
    echo "  stop        - Остановка системы"
    echo "  restart     - Перезапуск системы"
    echo "  status      - Показать статус системы"
    echo "  test        - Запуск тестов"
    echo "  cleanup     - Очистка системы"
    echo "  help        - Показать эту справку"
    echo
    echo "Примеры:"
    echo "  $0 install && $0 start"
    echo "  $0 restart"
    echo "  $0 status"
}

# Основная логика
main() {
    case "${1:-start}" in
        "install")
            log_info "🚀 Установка MAS системы..."
            check_environment
            create_directories
            install_python_deps
            start_docker_services
            init_database
            test_system
            log_success "🎉 Установка завершена! Используйте: $0 start"
            ;;
        "start")
            log_info "🚀 Запуск MAS системы..."
            check_environment
            create_directories
            start_docker_services
            init_database
            start_mas_system
            ;;
        "stop")
            stop_system
            ;;
        "restart")
            stop_system
            sleep 5
            main start
            ;;
        "status")
            show_status
            ;;
        "test")
            check_environment
            test_system
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Неизвестная команда: $1"
            show_help
            exit 1
            ;;
    esac
}

# Запуск
echo "=========================================="
echo "🤖 MAS System Deployment Script"
echo "=========================================="

main "$@"