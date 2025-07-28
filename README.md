# Root-MAS: Multi‑Agent System Platform

This repository contains the skeleton for a multi‑agent system (MAS) inspired by the architecture described in the project specification.  It is designed to be run on a VPS and extended over the course of several sprints.  The goal of this code is to provide a clean starting point with configuration files, prompt templates and a simple run script demonstrating the tiered LLM cascade logic.

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

1.  Install dependencies.  At minimum you will need Python 3.9+ and the `autogen` library.  Additional packages such as `pyyaml` and `redis` may be required depending on which features you enable.
2.  Set up your environment variables in a `.env` file at the project root.  This file should include API keys for OpenRouter, Yandex GPT, SpeechKit, Telegram, etc.
3.  Run an echo test:

    ```bash
    python run.py --goal "echo"
    ```

    The script will read `root_mas/root_mas/config/llm_tiers.yaml` and select a
    model from the cheapest tier to handle your goal.  It will then print which
    model would have been used.  In a real deployment the call to the large
    language model would occur here.

4.  Gradually extend the code base by implementing the stubs in `tools/` and
    adding additional agents and prompts as described in the specification.  See
    the `root_mas/root_mas/config/agents.yaml` file for a list of the core agents
    and their responsibilities.

## Notes

* This repository is intentionally lightweight and focuses on project scaffolding.  Many modules contain placeholder functions that need to be filled in during the development sprints.
* The `llm_tiers.yaml` file defines three tiers (cheap, standard and premium) with example model identifiers.  Adjust these values based on the models you have access to.
* Feel free to modify the directory structure or add additional configuration files as the project evolves.
