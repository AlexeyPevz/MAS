# Обзор API

Ниже перечислены ключевые модули Root‑MAS и их назначение.

| Модуль | Описание |
|--------|----------|
| `agents/` | Базовые классы и реализации корневых агентов. |
| `tools/smart_groupchat.py` | Интеллектуальное управление групповым чатом и маршрутизация сообщений между агентами. |
| `tools/cron.py` | Простая реализация планировщика задач на базе `schedule`. |
| `tools/prompt_builder.py` | Создание версий системных промптов, их аудит (diff) и сохранение в git. |
| `tools/llm_selector.py` | Выбор модели из каскада уровней LLM и переход между ними. |
| `tools/multitool.py` | Вызов сторонних API через фиксированную модель. |
| `tools/n8n_client.py` | Мини‑клиент для работы с n8n REST API. |
| `tools/webapp_builder.py` | Взаимодействие с GPT‑Pilot для генерации веб‑приложений. |
| `memory/` | Клиенты для Redis, PostgreSQL и ChromaDB. |
| `examples/init_db.py` | Применение SQL‑миграций для инициализации базы данных. |

Диаграмма архитектуры находится в файле [`architecture.svg`](architecture.svg). Она демонстрирует связи между слоями системы и внешними сервисами.

## HTTP эндпоинты

- `GET /` — базовая информация о сервисе
- `GET /docs` — Swagger UI
- `GET /pwa` — PWA интерфейс (статические файлы)
- `WS /ws` — WebSocket для визуализации мыслительного процесса
- `POST /api/v1/chat` — отправка сообщения в MAS
- `GET /api/v1/status` — статус системы
- `GET /api/v1/metrics/dashboard` — метрики для дашборда
- `GET /metrics` — Prometheus‑метрики (если установлен `prometheus_client`)

## AutoGen Studio Logger

Проект включает `tools/studio_logger.py`, который записывает JSONL‑логи в `logs/studio.jsonl`. При наличии переменных
`AUTOGEN_STUDIO_URL` и `AUTOGEN_STUDIO_API_KEY` логи можно отправить на внешний приёмник по адресу
`{AUTOGEN_STUDIO_URL}/api/v1/logs/upload`.
