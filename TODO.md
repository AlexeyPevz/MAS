# Root-MAS TODO

Ниже — дорожная карта доведения текущего репозитория до «production-ready».  
Задачи сгруппированы по приоритету. Выполняя их, отмечайте ✅.

## 0. CI / базовая инфраструктура
- [x] Добавить **GitHub Actions**: linters (`flake8`, `mypy`), `pytest`. (Docker-образ и GHCR остаётся)
- [ ] Подготовить **Dockerfile.prod** / `docker-compose.prod.yml` с зависимостями (Postgres, Redis, Prometheus).
- [ ] Настроить автопубликацию образа в **GHCR**.

## 1. Зависимости и базовое окружение
- [x] Обновить `requirements.txt` (✅ autogen добавлен).
- [ ] Проверить совместимые версии `python-telegram-bot`, `prometheus_client`, `requests`, `hvac`, `chromadb`.

## 2. Агентное ядро / AutoGen
- [x] Удалить fallback-классы в `agents/base.py` (ConversableAgent) при наличии AutoGen.
- [x] Удалить fallback-классы в `tools/groupchat_manager.py`.
- [ ] Пройтись по всем модулям, где `try … except ImportError` → убедиться, что настоящие импорты работают.
- [ ] Расширить структуру промптов:
  - system.md (базовая роль агента)
  - task_*.md (специализированные промпты под разные задачи)
  - optional: reflexion.md / critique.md для self-eval
- [ ] Подготовить расширенные промпты для ключевых агентов: meta, agent_builder, model_selector, coordination, prompt_builder.
- [ ] Обновить BaseAgent / PromptBuilder, чтобы могли загружать отдельные task-промпты по запросу.

## 3. Observability
- [x] Убедиться, что при наличии `prometheus_client` метрики регистрируются.
- [x] Добавить middleware для подсчёта токенов и ошибок в вызовах LLM.

## 4. Security / Secrets
- [x] Реализовать `security.get_secret` через HashiCorp Vault (HTTP API).
- [x] Добавить авто-refresh Vault token.
- [ ] `approve_global_prompt_change` — отправка diff в Telegram-бот, запись аудита в git.

## 5. Budget & LLM tiers
- [x] Считывать цены токенов из конфиг-файла (`config/pricing.yaml`).
- [x] `budget_manager` — метод `add_usage`, расчёт стоимости из Pricing.
- [x] Сохранять расходы в Redis (fallback CSV).
- [x] В `llm_selector.retry_with_higher_tier` — учитывать бюджет-менеджер.

## 6. Инструменты (tools/*)
- [x] `multitool.call_api` — экспоненциальный backoff, circuit-breaker.
- [x] `n8n_client` — auth-header, retry/backoff 5xx/timeout.
- [ ] `wf_builder` — формирование workflow нод на основе спецификации.
- [ ] `instance_factory` — health-check, rollback on failure.
- [ ] `researcher` — перейти на SerpAPI / Browserless, добавить кеш.
- [ ] `fact_checker` — GPT-powered пост-валидация фактов.
- [ ] `telegram_voice` — перевести на web-hooks, очереди для TTS.

## 7. Тесты
- [x] Unit-тесты на каждую tool-функцию (базовые mock-free проверки).
- [ ] Интеграционный тест: goal → groupchat → callback (docker-in-docker).

## 8. Документация
- [ ] Обновить `README.md`: архитектура, быстрый старт, эксплуатация.
- [ ] Сгенерировать диаграмму потоков (PlantUML / Mermaid) в `docs/`.

---
**Процесс:** создаём ветку / PR на каждую задачу, прогоняем CI, мержим.