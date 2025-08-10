# 🚀 Руководство по установке и запуску Root-MAS

## 📋 Содержание

1. [Системные требования](#системные-требования)
2. [Быстрый старт](#быстрый-старт)
3. [Детальная установка](#детальная-установка)
4. [Конфигурация](#конфигурация)
5. [Способы запуска](#способы-запуска)
6. [Проверка работоспособности](#проверка-работоспособности)
7. [Устранение проблем](#устранение-проблем)

## 🖥️ Системные требования

### Минимальные:
- Python 3.9-3.13
- 4GB RAM
- 2GB свободного места на диске
- Интернет-соединение

### Рекомендуемые:
- Python 3.11+
- 8GB RAM
- 10GB свободного места
- Redis сервер
- PostgreSQL 13+

### Опциональные сервисы:
- Docker и Docker Compose
- n8n (для workflow автоматизации)
- GPT-Pilot (для генерации приложений)

## ⚡ Быстрый старт

### Самый простой способ:

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourusername/root-mas.git
cd root-mas

# 2. Запустите автоматический установщик
chmod +x quickstart.sh
./quickstart.sh

# 3. Отредактируйте .env файл
nano .env  # Добавьте OPENAI_API_KEY

# 4. Запустите систему
./quickstart.sh api
```

**Готово!** API доступен на http://localhost:8000

## 🔧 Детальная установка

### Шаг 1: Подготовка окружения

```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

### Шаг 2: Установка зависимостей

```bash
# Обновление pip
pip install --upgrade pip

# Установка основных пакетов
pip install -r requirements.txt
```

### Шаг 3: Настройка конфигурации

```bash
# Копирование примера конфигурации
cp .env.example .env

# Создание необходимых директорий
mkdir -p data/{metrics,learning,events,knowledge_graph,federation,ab_tests}
mkdir -p logs
```

### Шаг 4: Установка внешних сервисов (опционально)

#### Redis:
```bash
# Ubuntu/Debian
sudo apt install redis-server

# macOS
brew install redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

#### PostgreSQL:
```bash
# Ubuntu/Debian
sudo apt install postgresql

# macOS
brew install postgresql

# Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:13
```

## ⚙️ Конфигурация

### Основные переменные окружения (.env):

```env
# ОБЯЗАТЕЛЬНЫЕ
OPENAI_API_KEY=sk-...              # Ваш OpenAI API ключ

# ОПЦИОНАЛЬНЫЕ
# Telegram интеграция
TELEGRAM_BOT_TOKEN=...              # Токен от @BotFather

# Базы данных
REDIS_HOST=localhost                # Redis хост
REDIS_PORT=6379                     # Redis порт
POSTGRES_HOST=localhost             # PostgreSQL хост
POSTGRES_PORT=5432                  # PostgreSQL порт
POSTGRES_DB=rootmas                 # Имя БД
POSTGRES_USER=postgres              # Пользователь БД
POSTGRES_PASSWORD=password          # Пароль БД

# Внешние сервисы
N8N_API_URL=http://localhost:5678      # n8n URL
N8N_API_KEY=...                         # n8n API ключ
GPT_PILOT_URL=http://localhost:7681    # GPT-Pilot URL
GPT_PILOT_API_KEY=...                   # GPT-Pilot API ключ

# Безопасность
MAS_SECRET_KEY=...                  # Будет сгенерирован автоматически
JWT_EXPIRATION_MINUTES=30           # Время жизни токена

# Лимиты
RATE_LIMIT_REQUESTS=100             # Запросов в минуту
RATE_LIMIT_WINDOW=60                # Окно в секундах
DAILY_BUDGET_LIMIT=10.0             # Дневной лимит в $
```

## 🚀 Способы запуска

### 1. Рекомендуемый способ - через quickstart.sh:

```bash
# Проверка системы
./quickstart.sh

# Запуск API сервера
./quickstart.sh api

# Запуск Telegram бота
./quickstart.sh telegram

# Запуск всей системы
./quickstart.sh all

# Тестовый запуск
./quickstart.sh test
```

### 2. Прямой запуск компонентов:

```bash
# API сервер (основной компонент)
python3 api/main.py

# Telegram бот (если настроен)
python3 tools/modern_telegram_bot.py

# Проверка системы
python3 check_system.py
```

### 3. Production запуск:

#### Через Docker Compose:
```bash
docker-compose up -d
```

#### Через systemd (Linux):
```bash
# Копирование service файла
sudo cp deployment/root-mas.service /etc/systemd/system/

# Редактирование пути к проекту
sudo nano /etc/systemd/system/root-mas.service

# Запуск
sudo systemctl daemon-reload
sudo systemctl enable root-mas
sudo systemctl start root-mas

# Проверка статуса
sudo systemctl status root-mas
```

#### Через supervisor:
```bash
python3 run_system.py
```

### 4. Режимы разработки:

```bash
# Запуск с автоперезагрузкой
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Запуск с отладкой
python3 -m debugpy --listen 5678 api/main.py
```

## ✅ Проверка работоспособности

### 1. Системная проверка:
```bash
python3 check_system.py
```

Должны быть зеленые галочки для:
- ✅ Все зависимости установлены
- ✅ Модули загружаются без ошибок
- ✅ Конфигурационные файлы на месте
- ✅ API ключи настроены

### 2. API проверка:
```bash
# Проверка health endpoint
curl http://localhost:8000/health

# Проверка документации
open http://localhost:8000/docs

# Тестовый запрос
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, MAS!"}'
```

### 3. Web интерфейс:
- PWA Dashboard: http://localhost:8000/pwa
- Swagger UI: http://localhost:8000/docs
- Метрики: http://localhost:8000/metrics

## 🔧 Устранение проблем

### Ошибка: "Module not found"
```bash
# Убедитесь, что venv активирован
source venv/bin/activate

# Переустановите зависимости
pip install -r requirements.txt --force-reinstall
```

### Ошибка: "OPENAI_API_KEY not set"
```bash
# Проверьте .env файл
cat .env | grep OPENAI_API_KEY

# Экспортируйте напрямую
export OPENAI_API_KEY=sk-...
```

### Ошибка: "Redis connection failed"
```bash
# Проверьте, запущен ли Redis
redis-cli ping

# Если нет, запустите
redis-server

# Или отключите Redis в .env
DISABLE_REDIS=true
```

### Ошибка: "Port 8000 already in use"
```bash
# Найдите процесс
lsof -i :8000

# Завершите его
kill -9 <PID>

# Или используйте другой порт
python3 api/main.py --port 8001
```

### Общие рекомендации:
1. Всегда используйте виртуальное окружение
2. Проверяйте логи в `logs/` директории
3. Запускайте `check_system.py` при проблемах
4. Обновляйте зависимости регулярно

## 📚 Дополнительные ресурсы

- [Архитектура системы](architecture.md)
- [Настройка агентов](agents_guide.md)
- [API документация](api_reference.md)
- [FAQ](faq.md)

## 🆘 Получение помощи

Если у вас возникли проблемы:

1. Проверьте [Issues](https://github.com/yourusername/root-mas/issues)
2. Создайте новый Issue с:
   - Описанием проблемы
   - Выводом `check_system.py`
   - Логами из `logs/`
   - Версией Python и ОС
3. Присоединяйтесь к [Discussions](https://github.com/yourusername/root-mas/discussions)

---

**Совет**: Начните с `./quickstart.sh api` - это самый простой способ запустить систему!