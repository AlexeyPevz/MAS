# Root-MAS: Multi-Agent System Platform

Root-MAS provides a lightweight yet production-ready skeleton for building a multi-agent system on top of AutoGen.  The platform ships with:

• A core set of specialised agents (Meta, Coordination, Model-Selector, Prompt-Builder, etc.)
• Plug-and-play tool integrations (n8n, ChromaDB, Redis, Vault, Prometheus)
• CI, Docker & GHCR pipelines for repeatable deployments
• A tiered LLM-cascade with budget awareness

The high-level message flow is visualised below (see [`docs/architecture.mmd`](docs/architecture.mmd)):

![architecture](https://raw.githubusercontent.com/any/placeholder/diagram.svg)

## Repository structure

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
├── production_launcher.py  # entry point for production MAS system
├── compose.yml             # compose template for a single client MAS
└── requirements.txt        # Python dependencies
```

## 🚀 Quick Start

### One-Command Deployment

1. **Clone & configure:**
   ```bash
   git clone <repo> root-mas && cd root-mas
   cp .env.example .env
   # Edit .env and add your OPENROUTER_API_KEY
   ```

2. **Install & start everything:**
   ```bash
   make install && make start
   ```
   
   Or using the deployment script directly:
   ```bash
   ./deploy.sh install
   ./deploy.sh start
   ```

3. **That's it!** 🎉 Your MAS system is running with:
   - All 12 agents initialized
   - PostgreSQL, Redis, ChromaDB running
   - Prometheus metrics on port 9000
   - Interactive interface ready

### Quick Commands

```bash
make status    # Check system status
make logs      # View logs
make restart   # Restart everything
make stop      # Stop system
make clean     # Clean up
```

## Manual deployment (dev environment)

1. **Install dependencies.**  Python 3.9 or newer is required.

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables.**  Copy `.env.example` to `.env` and fill in the API keys (`OPENROUTER_API_KEY`, `YANDEX_API_KEY`, `YANDEX_FOLDER_ID`, `N8N_API_TOKEN`, `TELEGRAM_BOT_TOKEN`).  Adjust connection settings for PostgreSQL, Redis and ChromaDB if needed.

3. **Start supporting services.**  Launch the containers with Docker Compose:

   ```bash
   cd deploy/internal
   cp .env.example .env  # adjust if needed
   docker compose up -d
   ```

   This starts PostgreSQL, Redis, ChromaDB and n8n.  For a client deployment use `deploy/client/compose.yml` or the top‑level `compose.yml`.

4. **Initialise the database (optional).**  Apply SQL migrations:

   ```bash
   python examples/init_db.py
   ```

5. **Run an echo test.**

   ```bash
   python production_launcher.py
   ```

   The script reads `config/llm_tiers.yaml` and prints which model would be chosen from the cheapest tier.

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
