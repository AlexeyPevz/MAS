.PHONY: install lint test build deploy start stop restart status clean help

# === Basic Commands ===
install:
	@echo "🚀 Установка MAS системы..."
	./deploy.sh install

start:
	@echo "▶️ Запуск системы..."
	./deploy.sh start

stop:
	@echo "⏹️ Остановка системы..."
	./deploy.sh stop

restart:
	@echo "🔄 Перезапуск системы..."
	./deploy.sh restart

status:
	@echo "📊 Статус системы..."
	./deploy.sh status

# === Development Commands ===
dev-install:
	@echo "🛠️ Установка для разработки..."
	pip3 install --break-system-packages -r requirements.txt
	pip3 install --break-system-packages python-dotenv pyyaml pytest flake8 mypy

lint:
	@echo "🔍 Проверка кода..."
	flake8 . --config=.flake8 || true
	mypy --ignore-missing-imports --explicit-package-bases . || true

test:
	@echo "🧪 Запуск тестов..."
	./deploy.sh test

# === Docker Commands ===
build:
	@echo "🏗️ Сборка Docker образа..."
	docker build -t mas-app .

deploy:
	@echo "🚀 Развертывание через Docker..."
	docker compose -f docker-compose.prod.yml up -d --build

deploy-integrations:
	@echo "🔗 Установка интеграций..."
	./deploy.sh install-integrations

stop-integrations:
	@echo "⏹️ Остановка интеграций..."
	./deploy.sh stop-integrations

# === Utility Commands ===
clean:
	@echo "🧹 Очистка системы..."
	./deploy.sh cleanup

logs:
	@echo "📜 Просмотр логов..."
	docker compose -f docker-compose.prod.yml logs -f

# === Quick Commands ===
quick-start: dev-install test start

quick-demo:
	@echo "🎭 Быстрое демо..."
	python3 production_launcher.py

# === Legacy Commands ===
run:
	@echo "⚠️ Используйте 'make start' вместо 'make run'"
	python3 production_launcher.py

# === Help ===
help:
	@echo "🤖 MAS System Makefile"
	@echo ""
	@echo "Основные команды:"
	@echo "  install      - Полная установка системы"
	@echo "  start        - Запуск системы"
	@echo "  stop         - Остановка системы"
	@echo "  restart      - Перезапуск системы"
	@echo "  status       - Статус системы"
	@echo ""
	@echo "Разработка:"
	@echo "  dev-install  - Установка для разработки"
	@echo "  lint         - Проверка кода"
	@echo "  test         - Запуск тестов"
	@echo "  build        - Сборка Docker образа"
	@echo ""
	@echo "Утилиты:"
	@echo "  clean        - Очистка системы"
	@echo "  logs         - Просмотр логов"
	@echo "  help         - Эта справка"
	@echo ""
	@echo "Быстрый старт:"
	@echo "  make install && make start"

# Default target
.DEFAULT_GOAL := help
