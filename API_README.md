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

# Для голосовых функций (опционально)
export YANDEX_API_KEY="your-yandex-api-key"
export YANDEX_FOLDER_ID="your-yandex-folder-id"
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

### Voice API (если настроен Yandex SpeechKit)
- `POST /api/v1/voice/stt` - Speech-to-Text (распознавание речи)
- `POST /api/v1/voice/tts` - Text-to-Speech (синтез речи)  
- `POST /api/v1/voice/chat` - Полный голосовой чат (STT + Chat + TTS)

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
1. Получает сообщения от пользователей (текст + голос)
2. Отправляет их в API (`/api/v1/chat/message` или `/api/v1/voice/chat`)
3. Получает ответы от Communicator Agent
4. Отправляет ответы пользователям (текст + голос)

**Голосовые функции работают если настроен Yandex SpeechKit!**

## 🔮 Дальнейшие шаги

### Для PWA:
1. ✅ **Готово!** Базовое PWA создано (`pwa/index.html`)
2. ✅ **Готово!** Подключено к API endpoints
3. ✅ **Готово!** Добавлен iframe для AutoGen Studio
4. ✅ **Готово!** Real-time через WebSocket
5. 🔄 **Запуск**: Сервируйте `pwa/` через HTTP сервер (например nginx)

**Откройте:** http://your-server/pwa/ для использования PWA!

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