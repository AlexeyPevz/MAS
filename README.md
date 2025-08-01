# Root-MAS: Multi-Agent System Platform 🤖

[![Python](https://img.shields.io/badge/python-3.9--3.13-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.5.1+-orange.svg)](https://github.com/microsoft/autogen)

Root-MAS provides a lightweight yet production-ready skeleton for building a multi-agent system on top of AutoGen v0.4+. The platform ships with:

• A core set of specialised agents (Meta, Coordination, Model-Selector, Prompt-Builder, etc.)
• RESTful API server with WebSocket support
• Integration bridges for Telegram, PWA, and other clients  
• PostgreSQL for persistent storage, Redis for caching, ChromaDB for embeddings
• Prometheus metrics and structured logging
• Easy deployment via Docker Compose or Kubernetes

The high-level message flow is visualised below (see [`docs/architecture.mmd`](docs/architecture.mmd)):

![architecture](https://raw.githubusercontent.com/any/placeholder/diagram.svg)

## 🚀 Быстрый старт

### 🎯 Запуск одной командой

#### Linux/macOS:
```bash
# Клонируйте репозиторий
git clone https://github.com/yourusername/root-mas.git
cd root-mas

# Запустите автоматическую установку и старт
./setup.sh
```

#### Windows/Любая ОС с Python:
```bash
# Клонируйте репозиторий
git clone https://github.com/yourusername/root-mas.git
cd root-mas

# Запустите универсальный установщик
python install_and_run.py
```

### ✅ Что происходит автоматически:

1. **Проверка окружения:**
   - Python версии (требуется 3.9-3.13)
   - Удаление старых версий AutoGen если есть

2. **Установка зависимостей:**
   - AutoGen v0.4+ (autogen-agentchat, autogen-ext)
   - Все необходимые библиотеки из requirements.txt

3. **Настройка конфигурации:**
   - Создание .env из .env.example
   - Проверка API ключей

4. **Запуск системы:**
   - API сервер на http://localhost:8000
   - Документация API на http://localhost:8000/docs
   - Telegram бот (если настроен токен)

### 📋 Минимальные требования:

- **Python 3.9-3.13** (AutoGen v0.4+ не поддерживает Python 3.14+)
- **API ключ OpenRouter** для работы LLM моделей
- 4GB RAM минимум
- 2GB свободного места на диске

### 🔧 Конфигурация:

1. **Скопируйте .env.example в .env:**
   ```bash
   cp .env.example .env
   ```

2. **Заполните обязательный API ключ:**
   ```bash
   # Откройте .env и добавьте ваш ключ
   OPENROUTER_API_KEY=your-actual-api-key-here
   ```

3. **Опциональные интеграции:**
   - `TELEGRAM_BOT_TOKEN` - для Telegram бота
   - `YANDEX_API_KEY` - для голосовых функций

### 🚀 Последующие запуски:

После первой установки используйте:

```bash
# Linux/macOS
./start.sh

# Windows
start.bat

# Или напрямую
python run_system.py
```

## 📁 Структура проекта

```
.
├── agents/                 # skeleton implementations of the core agents
├── config/                 # YAML configuration files
│   ├── agents.yaml         # definitions of root agents and their models
│   ├── llm_tiers.yaml      # model tiers (cheap/standard/premium)
│   ├── instances.yaml      # registry of deployed MAS instances
│   └── config_loader.py    # utility functions for loading configs
├── deploy/                 # docker compose templates
│   ├── internal/compose.yml  # compose for internal MAS instance
│   └── client/compose.yml    # compose for client MAS instance
├── docs/                   # architecture diagram and sprint plan
├── examples/               # demo scripts
├── memory/                 # storage backends (Redis, Postgres, Chroma)
├── prompts/                # system prompts for all agents
├── tools/                  # helper modules for integrations
├── run_system.py           # entry point for production MAS system
├── compose.yml             # compose template for a single client MAS
└── requirements.txt        # Python dependencies
```

## Operations & observability

The module `tools.observability` registers Prometheus metrics such as
token/ error counters and latency histograms.  Expose them by setting
the environment variable `PROMETHEUS_METRICS_PORT` (default 9000).

Health-checks: `docker compose ps` (integrated into Instance-Factory).

Backups: Postgres runs with a named volume `postgres-data`.  Schedule
`pg_dump` via `tools/cron.py`.

Budget tracking is enabled via `tools.budget_manager` and stored in Redis
(fallback CSV if Redis unavailable).

## Example scripts

Several demos under [`examples/`](examples) showcase common flows:

- [`examples/echo_demo.py`](examples/echo_demo.py) – interactive echo test using the model picker.
- [`examples/workflow_demo.py`](examples/workflow_demo.py) – generate and activate an n8n workflow.
- [`examples/webapp_demo.py`](examples/webapp_demo.py) – request a web application from GPT‑Pilot.
- [`examples/init_db.py`](examples/init_db.py) – apply SQL migrations for PostgreSQL.

Explore these scripts to understand how the helper modules in `tools/` are intended to work.

## Development notes

* Many modules are placeholders and should be expanded during future sprints.
* The model cascade in `config/llm_tiers.yaml` lists LLMs in order of cost.  Adjust it for your providers.
* Additional design documents are available in [`docs/`](docs). See
  [`docs/usage.md`](docs/usage.md) for usage examples and
  [`docs/api.md`](docs/api.md) for an overview of available modules.

## Approval process for critical changes

Changes to global prompts under `prompts/global` and all files in `deploy/`
require explicit approval. Pull requests touching these paths must have a
GPG-signed commit and must be reviewed by @AlexeyPevz before merging.
