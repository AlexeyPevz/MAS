# Root-MAS: Multi‑Agent System Platform

This repository contains a starting code base for a multi‑agent system (MAS) inspired by the architecture described in the project specification.  It is designed to be run on a VPS and extended over the course of several sprints.  The goal of this code is to provide a clean foundation with configuration files, prompt templates and a simple run script demonstrating the tiered LLM cascade logic.

## Project structure

```
root_mas/
├── config/                 # YAML configuration files
│   ├── agents.yaml         # definitions of core agents and their roles
│   ├── llm_tiers.yaml      # LLM tier definitions for cascade selection
│   └── instances.yaml      # placeholder for deployed MAS instances
├── prompts/
│   ├── global/
│   │   └── system.md       # global system prompt shared by all agents
│   └── agents/
│       └── meta/
│           └── system.md   # system prompt for the Meta agent (example)
├── tools/                  # helper modules that encapsulate integrations
│   ├── telegram_voice.py   # stub for Telegram bot with STT/TTS via Yandex
│   ├── n8n_client.py       # stub for interacting with n8n workflows
│   ├── gpt_pilot.py        # stub for GPT‑Pilot integration
│   └── prompt_io.py        # utilities for reading/writing prompt files
├── deploy/
│   ├── internal/compose.yml# docker compose template for internal MAS
│   └── client/compose.yml  # docker compose template for client MAS
├── run.py                  # entry point for running the root group chat
└── .gitignore             # ignore Python caches and environment files
```

## How to use

1.  **Install dependencies.**  Python 3.9+ is required.  Install packages from `root_mas/requirements.txt`:

    ```bash
    pip install -r root_mas/root_mas/requirements.txt
    ```

2.  **Configure environment variables.**  Copy `.env.example` to `.env` and fill in the API keys (`OPENROUTER_API_KEY`, `YANDEX_API_KEY`, `YANDEX_FOLDER_ID`, `N8N_API_TOKEN`, `TELEGRAM_BOT_TOKEN`).
3.  **Start supporting services.**  To launch a local MAS instance use Docker Compose:

    ```bash
    cd root_mas/root_mas/deploy/internal
    cp .env.example .env  # create if needed
    docker compose up -d
    ```

    This starts PostgreSQL, Redis, ChromaDB and n8n as described in `deploy/internal/compose.yml`.
4.  **Run an echo test:**

    ```bash
    python run.py --goal "echo"
    ```

    The script will read `config/llm_tiers.yaml` and select a model from the cheapest tier to handle your goal.  It will then print which model would have been used.  In a real deployment the call to the large language model would occur here.

5.  **Iterate on the agents.**  Gradually extend the code base by implementing the stubs in `tools/` and adding new agents and prompts.  See `config/agents.yaml` for a list of core agents and their roles.

## Notes

* This repository is intentionally lightweight and focuses on the initial setup.  Many modules contain placeholder functions that need to be filled in during the development sprints.
* The `llm_tiers.yaml` file defines three tiers (cheap, standard and premium) with example model identifiers.  Adjust these values based on the models you have access to.
* Feel free to modify the directory structure or add additional configuration files as the project evolves.
