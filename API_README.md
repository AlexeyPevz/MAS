# Root-MAS API System

Обновленная архитектура Root-MAS с единым API для всех клиентов.

## 🚀 Быстрый запуск

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

```bash
export OPENROUTER_API_KEY="your-key-here"
export TELEGRAM_BOT_TOKEN="your-bot-token"  # опционально
```

### 3. Запуск системы

```bash
python run_system.py
```

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │       PWA       │    │  Mini App (TG)  │
│                 │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI       │
                    │   REST + WS     │
                    └─────────┬───────┘
                              │
                ┌─────────────────────────┐
                │    MAS Integration      │
                │                         │
                └─────────┬───────────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │Communicator │ │    MAS      │ │ Data Layer  │
    │   Agent     │ │ GroupChat   │ │(Postgres,   │
    │             │ │             │ │ Redis, etc) │
    └─────────────┘ └─────────────┘ └─────────────┘
```

## 🔧 Исправленные проблемы

### ✅ Event Loop Issues
- Заменен устаревший `get_event_loop()` на `get_running_loop()`
- Улучшен graceful shutdown для всех компонентов
- Исправлены конфликты между sync/async callbacks

### ✅ API Integration
- Единый API для всех клиентов
- WebSocket для real-time обновлений
- Proper dependency injection
- Health checks и monitoring

## 📡 API Endpoints

### Chat API
- `POST /api/v1/chat/message` - Отправка сообщения Communicator Agent
- `GET /api/v1/chat/history` - История диалогов
- `WS /ws` - WebSocket для real-time

### Metrics API
- `GET /api/v1/metrics/dashboard` - Системные метрики
- `GET /api/v1/agents/status` - Статус агентов
- `GET /health` - Health check

### Projects API
- `GET /api/v1/projects` - Список проектов
- `GET /api/v1/logs` - Системные логи

### AutoGen Studio Integration
- `GET /api/v1/studio/logs` - Прокси для Studio логов

## 🎯 Режимы запуска

```bash
# Полная система (API + MAS + Telegram)
python run_system.py

# Только API
RUN_MODE=api python run_system.py

# API без Telegram бота
unset TELEGRAM_BOT_TOKEN && python run_system.py
```

## 📊 Мониторинг

- **API документация**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health  
- **Metrics**: http://localhost:8000/api/v1/metrics/dashboard

## 🤖 Telegram Bot

Бот теперь работает через API:
1. Получает сообщения от пользователей
2. Отправляет их в API (`/api/v1/chat/message`)
3. Получает ответы от Communicator Agent
4. Отправляет ответы пользователям

## 🔮 Дальнейшие шаги

### Для PWA:
1. Создать React/Vue.js приложение
2. Подключить к API endpoints
3. Добавить iframe для AutoGen Studio
4. Реализовать real-time через WebSocket

### Для Telegram Mini App:
1. Использовать Telegram WebApp API
2. Подключить к тем же API endpoints
3. Адаптировать UI под Telegram

### Для полной замены AutoGen Studio:
1. Постепенно переносить функции Studio в PWA
2. Использовать API для получения данных
3. Создать лучший UX

## ⚡ Преимущества новой архитектуры

- ✅ **Единая точка входа** - все через API
- ✅ **Исправленные проблемы с Event Loop**
- ✅ **Масштабируемость** - легко добавлять новые клиенты
- ✅ **Real-time** - WebSocket для живых обновлений
- ✅ **Мониторинг** - встроенные метрики и health checks
- ✅ **Graceful shutdown** - корректная остановка всех компонентов

Теперь можете безопасно заменить развернутую систему на эту! 🎉