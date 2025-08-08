# 🚀 Руководство по быстрому старту

## Установка

### Способ 1: Автоматическая установка (рекомендуется)

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourusername/root-mas.git
cd root-mas

# 2. Запустите установщик
python install_and_run.py
```

Установщик автоматически:
- ✅ Проверит версию Python (нужен 3.9-3.13)
- ✅ Установит все зависимости включая AutoGen v0.4+
- ✅ Создаст файл конфигурации .env
- ✅ Запустит систему

### Способ 2: Для Linux/Mac

```bash
./setup.sh   # Полная установка с виртуальным окружением
```

### Способ 3: Ручная установка

```bash
# Установите зависимости
pip install -r requirements.txt

# Создайте конфигурацию
cp .env.example .env

# Запустите систему
python run_system.py
```

## Конфигурация

### Обязательные настройки

Откройте `.env` и добавьте API ключ:
```
OPENROUTER_API_KEY=sk-or-v1-ваш-ключ-здесь
```

Получить ключ: https://openrouter.ai/keys

### Опциональные настройки

```bash
# Telegram бот
TELEGRAM_BOT_TOKEN=токен-от-BotFather

# Режим запуска
RUN_MODE=full         # full, api, mas
ENVIRONMENT=production # production, development

# AutoGen Studio logger (внешний приёмник логов)
# AUTOGEN_STUDIO_URL=http://studio-host:8081
# AUTOGEN_STUDIO_API_KEY=your-studio-key
```

## Использование

### API и интерфейс

После запуска доступны:
- http://localhost:8000 — API сервер
- http://localhost:8000/docs — Swagger документация
- http://localhost:8000/pwa — PWA интерфейс (или http://localhost:8000/app → редирект)
- http://localhost:8000/metrics — Prometheus метрики

### Примеры запросов

```bash
# Отправить сообщение агентам
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Привет!"}'

# Проверить статус
curl http://localhost:8000/api/v1/status
```

### Telegram бот

Если настроен `TELEGRAM_BOT_TOKEN`:
1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Общайтесь с агентами через бота

## Управление

### Проверка системы
```bash
python quick_test.py
```

### Последующие запуски
```bash
./start.sh           # Linux/Mac
start.bat            # Windows  
python run_system.py # Универсальный
```

### Просмотр логов
```bash
tail -f logs/*.log
```

### Остановка
```
Ctrl+C
```

## Docker

### Запуск в Docker
```bash
docker-compose up -d
```

### Остановка
```bash
docker-compose down
```

## Решение проблем

### Python версия не подходит
- Требуется Python 3.9-3.13
- AutoGen v0.4+ не поддерживает Python 3.14+

### Ошибка установки зависимостей
```bash
pip install --upgrade pip
pip install autogen-agentchat>=0.5.1 autogen-ext[openai]>=0.5.5
```

### API ключ не работает
1. Проверьте правильность ключа в .env
2. Убедитесь что ключ активен на OpenRouter
3. Проверьте баланс на счету

### Агенты не отвечают
- Проверьте логи на ошибки
- Запустите `python test_autogen_v04.py`
- Система автоматически использует fallback режим

## Дополнительно

- [Примеры использования](examples/)
- [Техническая документация](docs/)
- [API Reference](http://localhost:8000/docs)
