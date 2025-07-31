# 🚀 Root-MAS Quick Start Guide

Полное руководство по запуску системы с решением всех проблем.

## 🔧 1. Решение проблемы с логами (КРИТИЧНО!)

### ⚠️ Проблема: Логи забивают 15GB за 2 часа

**НЕМЕДЛЕННО выполните:**

```bash
# Экстренная очистка всех логов
python3 cleanup_logs.py

# Или ручная очистка
rm -rf logs/*.log*
find . -name "*.log*" -size +100M -delete
```

**Постоянное решение:**

```bash
# Для продакшена (минимум логов)
export ENVIRONMENT=production
export LOG_LEVEL=WARNING

# Для разработки (больше логов, но контролируемо)
export ENVIRONMENT=development  
export LOG_LEVEL=INFO
```

## 🎤 2. Настройка SpeechKit (голосовые функции)

### ✅ У вас уже есть Yandex Cloud + SpeechKit

Просто добавьте переменные окружения (те же что и для Yandex GPT):

```bash
export YANDEX_API_KEY="your-yandex-api-key"
export YANDEX_FOLDER_ID="your-yandex-folder-id"
```

**Проверить настройку:**
```bash
python3 test_speechkit.py
```

**"Если настроен" означает:** Просто проверка этих переменных. Если есть - голос работает, если нет - только текст.

## 🔑 3. Исправление проблем с OpenAI API

### ✅ Уже исправлено в новой версии

Используйте ТОЛЬКО эти переменные:

```bash
# ОБЯЗАТЕЛЬНО
export OPENROUTER_API_KEY="your-openrouter-key"

# ОПЦИОНАЛЬНО
export YANDEX_API_KEY="your-yandex-key"      # для голоса
export YANDEX_FOLDER_ID="your-folder-id"     # для голоса
export TELEGRAM_BOT_TOKEN="your-bot-token"   # для Telegram

# НЕ НУЖНО (удалите если есть):
# export OPENAI_API_KEY="..."  ❌
```

## 🚀 4. Запуск системы

### Быстрый запуск:

```bash
# Установка зависимостей (если нужно)
pip3 install --break-system-packages fastapi uvicorn aiohttp

# Настройка переменных
export OPENROUTER_API_KEY="your-key"
export ENVIRONMENT=production  # для минимума логов

# Запуск
python3 run_system.py
```

### Доступные режимы:

```bash
# Полная система (API + MAS + Telegram)
python3 run_system.py

# Только API сервер
RUN_MODE=api python3 run_system.py

# Без Telegram бота
unset TELEGRAM_BOT_TOKEN && python3 run_system.py
```

## 📊 5. Проверка работы системы

### API Endpoints:
- **API документация:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health
- **Чат:** `POST /api/v1/chat/message`
- **Голос:** `POST /api/v1/voice/chat` (если настроен SpeechKit)

### PWA приложение:
Откройте `pwa/index.html` в браузере или сервируйте через веб-сервер.

### Telegram Bot:
Если настроен `TELEGRAM_BOT_TOKEN` - бот автоматически запустится.

## 🐛 6. Решение проблем

### Проблема: Event Loop ошибки
✅ **Исправлено** в новой версии - заменен `get_event_loop()` на `get_running_loop()`

### Проблема: Логи забивают диск
```bash
# Мониторинг логов
python3 -c "from tools.logging_config import log_monitor; log_monitor()"

# Очистка логов
python3 cleanup_logs.py

# Настройка продакшена
export ENVIRONMENT=production
```

### Проблема: SpeechKit не работает
```bash
# Проверка настроек
python3 test_speechkit.py

# Если API Key правильный, но не работает:
# 1. Проверьте включен ли SpeechKit в Yandex Cloud
# 2. Проверьте квоты и биллинг
# 3. Проверьте права сервисного аккаунта
```

### Проблема: OpenAI API ошибки
```bash
# Убедитесь что используете только OpenRouter
echo $OPENROUTER_API_KEY  # должен быть установлен
echo $OPENAI_API_KEY      # должен быть пустым

# Проверка конфигурации
python3 tools/llm_config.py
```

## 📂 7. Структура проекта после обновления

```
.
├── api/                     # Новый API сервер
│   ├── main.py             # FastAPI приложение  
│   └── integration.py      # Интеграция с MAS
├── pwa/                    # PWA приложение
│   ├── index.html          # Основной интерфейс
│   └── manifest.json       # PWA манифест
├── tools/
│   ├── logging_config.py   # Правильное логирование
│   ├── yandex_speechkit.py # SpeechKit интеграция
│   └── telegram_api_client.py # Telegram через API
├── run_system.py           # Главный launcher
├── cleanup_logs.py         # Очистка логов
├── test_speechkit.py       # Тест голоса
└── QUICK_START.md          # Этот файл
```

## ✅ 8. Что работает в новой версии

- ✅ **Исправлены проблемы Event Loop** в Telegram боте
- ✅ **Единый API** для всех клиентов (PWA, Telegram, Mini App)
- ✅ **Контроль логов** с автоматической ротацией
- ✅ **SpeechKit интеграция** для голосовых функций
- ✅ **Только OpenRouter** для LLM (никаких OpenAI ссылок)
- ✅ **PWA приложение** с красивым интерфейсом
- ✅ **AutoGen Studio** интеграция через iframe
- ✅ **Real-time** обновления через WebSocket
- ✅ **Graceful shutdown** всех компонентов

## 🎯 9. Быстрая миграция с сервера

1. **Остановите старую систему**
2. **Сделайте бэкап данных** (если есть база данных)
3. **Скопируйте новый код**
4. **Настройте правильные переменные окружения**
5. **Запустите новую систему**

```bash
# На сервере
cd /path/to/root-mas
git pull  # или скопируйте новые файлы

# Очистите старые логи
python3 cleanup_logs.py

# Настройте переменные
export OPENROUTER_API_KEY="your-key"
export ENVIRONMENT=production

# Запустите
python3 run_system.py
```

## 🎉 10. Результат

После выполнения всех шагов у вас будет:

- 🚀 **Стабильная система** без проблем с логами и event loop
- 🎤 **Голосовые функции** через Yandex SpeechKit
- 📱 **PWA приложение** для красивого интерфейса
- 🤖 **Telegram Bot** через API
- 📊 **Мониторинг и метрики**
- 🔧 **Легкое масштабирование** через единый API

**Теперь можете безопасно заменить развернутую систему!** 🎯