# Root-MAS TODO

Ниже — дорожная карта доведения текущего репозитория до «production-ready».  
Задачи сгруппированы по приоритету. Выполняя их, отмечайте ✅.

## 0. CI / базовая инфраструктура
- [ ] Добавить **GitHub Actions**: linters (`flake8`, `mypy`), `pytest` + сборка Docker-образа.
- [ ] Подготовить **Dockerfile.prod** / `docker-compose.prod.yml` с зависимостями (Postgres, Redis, Prometheus).
- [ ] Настроить автопубликацию образа в **GHCR**.

## 1. Зависимости и базовое окружение
- [ ] Обновить `requirements.txt` (✅ autogen добавлен).
- [ ] Проверить совместимые версии `python-telegram-bot`, `prometheus_client`, `requests`, `hvac`, `chromadb`.

## 2. Агентное ядро / AutoGen
- [ ] Удалить fallback-классы в `agents/base.py` (ConversableAgent) при наличии AutoGen.
- [ ] Удалить fallback-классы в `tools/groupchat_manager.py`.
- [ ] Пройтись по всем модулям, где `try … except ImportError` → убедиться, что настоящие импорты работают.

## 3. Observability
- [ ] Убедиться, что при наличии `prometheus_client` метрики регистрируются.
- [ ] Добавить middleware для подсчёта токенов и ошибок в вызовах LLM.

## 4. Security / Secrets
- [ ] Реализовать `security.get_secret` через HashiCorp Vault (HTTP API).
- [ ] Добавить авто-refresh Vault token.
- [ ] `approve_global_prompt_change` — отправка diff в Telegram-бот, запись аудита в git.

## 5. Budget & LLM tiers
- [ ] Считывать цены токенов из конфиг-файла (`config/pricing.yaml`).
- [ ] `budget_manager` — сохранять расходы в Postgres/Redis.
- [ ] В `llm_selector.retry_with_higher_tier` — учитывать бюджет-менеджер.

## 6. Инструменты (tools/*)
- [ ] `multitool.call_api` — экспоненциальный backoff, circuit-breaker.
- [ ] `n8n_client` — auth-header, paginated requests, retry 502/504.
- [ ] `wf_builder` — формирование workflow нод на основе спецификации.
- [ ] `instance_factory` — health-check, rollback on failure.
- [ ] `researcher` — перейти на SerpAPI / Browserless, добавить кеш.
- [ ] `fact_checker` — GPT-powered пост-валидация фактов.
- [ ] `telegram_voice` — перевести на web-hooks, очереди для TTS.

## 7. Тесты
- [ ] Unit-тесты на каждую tool-функцию (mock external requests).
- [ ] Интеграционный тест: goal → groupchat → callback (docker-in-docker).

## 8. Документация
- [ ] Обновить `README.md`: архитектура, быстрый старт, эксплуатация.
- [ ] Сгенерировать диаграмму потоков (PlantUML / Mermaid) в `docs/`.

---
**Процесс:** создаём ветку / PR на каждую задачу, прогоняем CI, мержим.