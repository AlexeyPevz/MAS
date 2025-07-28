# Root-MAS: Multi-Agent System Platform

Root-MAS provides a lightweight skeleton for building a multi-agent system with AutoGen.  The project includes configuration templates, system prompts and demo scripts that illustrate the tiered LLM cascade described in the documentation.

## Repository structure

```
.
├── agents/                 # skeleton implementations of the core agents
├── config/                 # YAML configuration files
│   ├── agents.yaml         # definitions of root agents and their models
│   ├── llm_tiers.yaml      # model tiers (cheap/standard/premium)
│   └── instances.yaml      # registry of deployed MAS instances
├── deploy/                 # docker compose templates
│   ├── internal/compose.yml  # compose for internal MAS instance
│   └── client/compose.yml    # compose for client MAS instance
├── docs/                   # architecture diagram and sprint plan
├── examples/               # demo scripts
├── memory/                 # storage backends (Redis, Postgres, Chroma)
├── prompts/                # system prompts for all agents
├── tools/                  # helper modules for integrations
├── run.py                  # entry point that launches the root group chat
├── compose.yml             # compose template for a single client MAS
└── requirements.txt        # Python dependencies
```

## Deployment

1. **Install dependencies.**  Python 3.9 or newer is required.

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables.**  Copy `.env.example` to `.env` and fill in the API keys (`OPENROUTER_API_KEY`, `YANDEX_API_KEY`, `YANDEX_FOLDER_ID`, `N8N_API_TOKEN`, `TELEGRAM_BOT_TOKEN`).  Adjust connection settings for PostgreSQL, Redis and ChromaDB if needed.  Secrets may also be stored in HashiCorp Vault using `VAULT_ADDR`, `VAULT_TOKEN` and `VAULT_PATH`.

3. **Start supporting services.**  Launch the containers with Docker Compose.  For an internal instance run:

   ```bash
   cd deploy/internal
   cp .env.example .env  # adjust if needed
   docker compose up -d
   ```

   This starts PostgreSQL, Redis, ChromaDB and n8n.  For a client deployment use `deploy/client/compose.yml` or the top-level `compose.yml`.

4. **Initialise the database.**  Once the services are running, apply the SQL migrations:

   ```bash
   python examples/init_db.py
   ```

5. **Run an echo test.**

   ```bash
   python run.py --goal "echo"
   ```

   The script reads `config/llm_tiers.yaml` and prints which model would be chosen from the cheapest tier.

## Example scripts

Several demos under [`examples/`](examples) showcase common flows:

- [`examples/echo_demo.py`](examples/echo_demo.py) – interactive echo test using the model picker.
- [`examples/workflow_demo.py`](examples/workflow_demo.py) – generate and activate an n8n workflow.
- [`examples/webapp_demo.py`](examples/webapp_demo.py) – request a web application from GPT-Pilot.
- [`examples/init_db.py`](examples/init_db.py) – apply SQL migrations for PostgreSQL.

Explore these scripts to understand how the helper modules in `tools/` are intended to work.

## Observability

Prometheus and Grafana services are included under `deploy/internal`. Run `docker compose up -d` in that directory and the metrics endpoint at `autogen:9000` will be scraped automatically. Refer to [`docs/observability.md`](docs/observability.md) for details on dashboards and alerting.

## Development notes

* Many modules are placeholders and should be expanded during future sprints.
* The model cascade in `config/llm_tiers.yaml` lists LLMs in order of cost.  Adjust it for your providers.
* Additional design documents are available in [`docs/`](docs). See
  [`docs/usage.md`](docs/usage.md) for usage examples and
  [`docs/api.md`](docs/api.md) for an overview of available modules.

## Approval process for critical changes

Changes to global prompts under `prompts/global` and all files in `deploy/` require explicit approval. Pull requests touching these paths must have a GPG-signed commit and must be reviewed by @AlexeyPevz before merging.
