# Обзор API

## RESTful API Endpoints

MAS система предоставляет RESTful API для внешних интеграций на порту 8080 (по умолчанию).

### Основные endpoints:

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/health` | GET | Проверка состояния системы |
| `/api/v1/status` | GET | Детальный статус системы и агентов |
| `/api/v1/models` | GET | Список доступных LLM моделей |
| `/api/v1/messages` | POST | Отправка сообщения в MAS |
| `/api/v1/messages/history` | GET | История сообщений |
| `/api/v1/agents` | GET | Список всех агентов |
| `/api/v1/agents/{name}` | GET | Информация о конкретном агенте |
| `/api/v1/tasks` | POST | Создание новой задачи |
| `/api/v1/tasks` | GET | Список активных задач |
| `/api/v1/tasks/{id}` | GET | Информация о задаче |
| `/api/v1/budget` | GET | Информация о бюджете |
| `/api/v1/statistics` | GET | Статистика системы |
| `/api/v1/webhooks/telegram` | POST | Webhook для Telegram |

### Примеры использования:

```bash
# Отправка сообщения
curl -X POST http://localhost:8080/api/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Создай план проекта", "user_id": "api_user"}'

# Получение статуса
curl http://localhost:8080/api/v1/status

# Создание задачи
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"description": "Исследовать новые технологии ИИ", "agent": "researcher"}'
```

## Ключевые модули

| Модуль | Описание |
|--------|----------|
| `agents/` | Базовые классы и реализации корневых агентов |
| `tools/api_server.py` | RESTful API сервер для внешних интеграций |
| `tools/smart_groupchat.py` | Интеллектуальное управление групповым чатом и маршрутизация |
| `tools/modern_telegram_bot.py` | Современный Telegram бот с поддержкой команд и статистики |
| `tools/speechkit_client.py` | Клиент для Yandex SpeechKit (STT/TTS) |
| `tools/communicator.py` | Агент-коммуникатор для взаимодействия с пользователями |
| `tools/cron.py` | Простая реализация планировщика задач |
| `tools/prompt_builder.py` | Создание версий системных промптов |
| `tools/llm_selector.py` | Выбор модели из каскада уровней LLM |
| `tools/multitool.py` | Вызов сторонних API |
| `tools/n8n_client.py` | Клиент для работы с n8n REST API |
| `tools/webapp_builder.py` | Взаимодействие с GPT‑Pilot |
| `memory/` | Клиенты для Redis, PostgreSQL и ChromaDB |
| `production_launcher.py` | Основная точка входа для production развертывания |

## Архитектура

Диаграмма архитектуры находится в файле [`architecture.svg`](architecture.svg). Она демонстрирует связи между слоями системы и внешними сервисами.
