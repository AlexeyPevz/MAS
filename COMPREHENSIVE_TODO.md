# 🎯 Комплексный TODO по результатам Code Review

## 🚨 КРИТИЧЕСКИЕ (P0) - Исправить немедленно!

### 1. Безопасность и секреты
- [ ] **УДАЛИТЬ .secret_key из репозитория** (файл содержит `TdXLojSLcAh3n8rmfJszhEa8a77v7bDSE0ooiwiwI5A`)
  ```bash
  git rm --cached .secret_key
  echo ".secret_key" >> .gitignore
  git commit -m "Remove secret key from repository"
  ```
- [ ] **Заменить SHA-256 на bcrypt/argon2** для хеширования паролей в `api/security.py`
- [ ] **Закрыть открытую выдачу JWT токенов** - требовать `X-Admin-Secret` всегда
- [ ] **Заменить pickle на JSON** в Redis для semantic cache (`tools/semantic_llm_cache.py`)
- [ ] **Исправить путь к secret_key** - использовать относительный путь или env вместо `/workspace/.secret_key`

### 2. Критические баги в коде
- [ ] **Исправить порядок объявлений в `api/security.py`** - перенести `class Role` выше `TokenData` (строки 111→54)
- [ ] **Удалить несуществующие импорты** в `api/main.py`:
  ```python
  # Удалить эти строки (35-41):
  from tools.multitool import (
      list_instances, get_instance_versions, rollback_instance,  # НЕ СУЩЕСТВУЮТ!
  )
  ```
- [ ] **Исправить вызов несуществующей функции** в voice endpoint (строка 489):
  ```python
  # Заменить:
  chat_response = await send_message(chat_msg)  # ФУНКЦИЯ НЕ ОПРЕДЕЛЕНА
  # На:
  response_text = await mas_integration.process_message(text, user_id)
  chat_response = ChatResponse(response=response_text, timestamp=time.time())
  ```

### 3. CORS и безопасность API
- [ ] **Исправить небезопасную CORS конфигурацию**:
  ```python
  # Заменить в api/main.py (305-312):
  app.add_middleware(
      CORSMiddleware,
      allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
      allow_credentials=False,  # или True только с конкретными origins
      allow_methods=["GET", "POST"],
      allow_headers=["Authorization", "Content-Type"],
  )
  ```

## 🔥 ВЫСОКИЙ ПРИОРИТЕТ (P1) - Исправить в течение недели

### 4. Авторизация и доступ
- [ ] **Защитить чувствительные endpoints** с помощью `Depends(require_permission)`:
  - [ ] `/api/v1/registry/*/rollback` - только admin
  - [ ] `/api/v1/cache/*` - требует авторизации
  - [ ] `/api/v1/federation/*` - требует роли admin/agent
  - [ ] `/metrics` - ограничить внутренней сетью или ролью
  - [ ] WebSocket endpoints - добавить проверку токена

### 5. Конфигурация и пути
- [ ] **Унифицировать пути хранения данных** - заменить хардкод `/workspace/data` на:
  ```python
  DATA_DIR = os.getenv("DATA_PATH", "/app/data")
  ```
  В файлах:
  - `tools/learning_loop.py`
  - `tools/knowledge_graph.py`
  - `tools/federated_learning.py`
  - `tools/quality_metrics.py`

### 6. Production настройки
- [ ] **Убрать reload=True из production** в `api/main.py` (строка 1261)
- [ ] **Исправить Dockerfile CMD** для production:
  ```dockerfile
  CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
  ```

### 7. Валидация данных
- [ ] **Добавить валидацию входных данных** во всех API endpoints используя Pydantic:
  ```python
  class ChatMessage(BaseModel):
      message: str = Field(..., min_length=1, max_length=10000)
      user_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
  ```

## 📋 СРЕДНИЙ ПРИОРИТЕТ (P2) - В течение 2-3 недель

### 8. Рефакторинг и архитектура
- [ ] **Разбить монолитный `api/main.py`** (1272 строки) на роутеры:
  - [ ] `routers/chat.py`
  - [ ] `routers/auth.py`
  - [ ] `routers/metrics.py`
  - [ ] `routers/registry.py`
  - [ ] `routers/federation.py`
  - [ ] `routers/voice.py`
  - [ ] `routers/websocket.py`

### 9. Тестирование
- [ ] **Написать unit тесты** для критических компонентов (довести покрытие до 80%)
- [ ] **Добавить тесты** для:
  - [ ] Импортов API (ловить ImportError)
  - [ ] Voice endpoints
  - [ ] Security и TokenData
  - [ ] CORS политик
  - [ ] WebSocket авторизации

### 10. CI/CD Pipeline
- [ ] **Создать GitHub Actions workflow** (`.github/workflows/ci.yml`):
  ```yaml
  - Linting (flake8, black)
  - Type checking (mypy)
  - Unit tests (pytest)
  - Coverage report
  - Docker build
  - Security scan (bandit)
  ```

### 11. Исправление багов
- [ ] **Исправить knowledge_graph.get_statistics**:
  ```python
  # Заменить:
  "relation_types": dict(nx.get_edge_attributes(self.graph, 'type').values())
  # На:
  from collections import Counter
  "relation_types": dict(Counter(nx.get_edge_attributes(self.graph, 'type').values()))
  ```
- [ ] **Добавить поддержку X-Forwarded-For** для rate limiting
- [ ] **Исправить Redis URL** в semantic cache - читать из env

### 12. Docker оптимизация
- [ ] **Унифицировать версии Python** (сейчас 3.10 и 3.11 в разных Dockerfile)
- [ ] **Оптимизировать слои Docker** - сначала зависимости, потом код
- [ ] **Добавить healthcheck** во все сервисы docker-compose

## 🎨 НИЗКИЙ ПРИОРИТЕТ (P3) - В течение месяца

### 13. Производительность
- [ ] **Добавить connection pooling** для БД и внешних API
- [ ] **Реализовать retry механизм** с exponential backoff для внешних сервисов
- [ ] **Добавить Circuit Breaker** для внешних API
- [ ] **Оптимизировать semantic cache** - добавить LRU eviction

### 14. Мониторинг и логирование
- [ ] **Настроить структурированное логирование** через python-json-logger
- [ ] **Добавить correlation ID** для трассировки запросов
- [ ] **Создать Grafana дашборды** для Prometheus метрик
- [ ] **Добавить OpenTelemetry** для distributed tracing

### 15. Документация
- [ ] **Создать отсутствующие файлы документации**:
  - [ ] `docs/architecture.md`
  - [ ] `docs/registry.md`
  - [ ] `docs/api_reference.md`
  - [ ] `docs/federation.md`
- [ ] **Добавить OpenAPI схемы** для всех моделей
- [ ] **Создать диаграммы архитектуры** (C4 model)

### 16. Качество кода
- [ ] **Настроить pre-commit hooks**:
  - [ ] black (форматирование)
  - [ ] isort (сортировка импортов)
  - [ ] flake8 (линтинг)
  - [ ] mypy (type checking)
- [ ] **Рефакторинг длинных функций** (> 50 строк)
- [ ] **Добавить type hints** во все публичные API

### 17. DevOps улучшения
- [ ] **Автоматизировать деплой** через CI/CD вместо deploy.sh
- [ ] **Настроить автоматическое резервное копирование** БД
- [ ] **Добавить мониторинг дискового пространства** для логов

## 📊 Метрики успеха

После выполнения всех задач:
- ✅ Тестовое покрытие > 80%
- ✅ Все критические уязвимости закрыты
- ✅ Время старта системы < 30 секунд
- ✅ API latency p99 < 500ms
- ✅ Документация покрывает 100% публичных API
- ✅ CI/CD pipeline полностью автоматизирован

## 🔄 Порядок выполнения

1. **Немедленно**: P0 задачи (безопасность, критические баги)
2. **Неделя 1**: Начать P1 задачи (авторизация, конфигурация)
3. **Неделя 2-3**: Завершить P1, начать P2 (рефакторинг, тесты)
4. **Месяц**: P3 задачи параллельно с текущей разработкой

---

*Этот TODO объединяет ВСЕ замечания из 4 независимых code review отчетов*