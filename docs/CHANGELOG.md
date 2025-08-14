# Changelog

## Unreleased
- Align project with AutoGen v0.9+ (message types, model client hints, docs)
- Dynamic agents: add runtime registration/unregistration helpers in `tools/smart_groupchat.py`
- AgentBuilder updated to create/register agents via `BaseAgent` (no legacy pyautogen)
- Versioned registry with persistence (file/Redis): tools, workflows, apps
  - APIs: `register_*_version`, `list_*`, `get_*_versions`, `rollback_*`
  - Storage: JSON file `data/registry.json` or Redis when `REGISTRY_BACKEND=redis`
- WF-Builder & WebApp-Builder register artifacts into registry
- REST endpoints for registry: list/versions/rollback
- PWA page `pwa/registry.html` to browse and rollback versions
- Validation layer `tools/validation.py` (workflow/app/tool) and light docs-url smoke test for tools
- Bug fixes & robustness:
  - Semantic cache: safe Redis-less mode, Chroma import fix
  - SpeechKit env unified (YANDEX_API_KEY / YANDEX_FOLDER_ID)
  - Removed hard-coded agent counts from API/PWA
  - Safer prompt loading (default text when file absent)