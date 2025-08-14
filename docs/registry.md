# Registry (Tools / Workflows / Apps)

Root-MAS tracks available resources (tools, n8n workflows, GPT‑Pilot apps) in a versioned registry.

## Storage backends
- File (default): `data/registry.json`
- Redis (optional): set `REGISTRY_BACKEND=redis` (honors `REDIS_HOST`, `REDIS_PORT`, `REGISTRY_REDIS_DB`)

## Programmatic API (Python)
- Register new version: `register_tool_version(name, meta)` / `register_workflow_version(id, meta)` / `register_app_version(id, meta)`
- Read current versions: `list_tools()` / `list_workflows()` / `list_apps()`
- Read all versions: `get_tool_versions(name)` / `get_workflow_versions(id)` / `get_app_versions(id)`
- Rollback: `rollback_tool(name, target_version)` / `rollback_workflow(id, target_version)` / `rollback_app(id, target_version)`

Each entry stores `current_version`, `versions` map, `max_versions` (default 5). Old versions are pruned automatically.

## REST API
- GET `/api/v1/registry/tools|workflows|apps` — current versions
- GET `/api/v1/registry/tools/{name}/versions` — all versions of tool
- GET `/api/v1/registry/workflows/{id}/versions` — all versions of workflow
- GET `/api/v1/registry/apps/{id}/versions` — all versions of app
- POST `/api/v1/registry/tools/{name}/rollback?target_version=N` — rollback to N (or previous if omitted)
- POST `/api/v1/registry/workflows/{id}/rollback?target_version=N`
- POST `/api/v1/registry/apps/{id}/rollback?target_version=N`

## PWA
- Page: `/pwa/registry.html` — browse current versions, expand all versions, rollback via UI.

## Integrations
- WF‑Builder automatically registers new versions after n8n activation
- WebApp‑Builder registers new versions after GPT‑Pilot task creation
- Tool registration callback (`REGISTER_TOOL`) records versions and can run a light docs-url smoke test

## Notes
- For production, consider moving registry to Redis (or RDBMS) for multi-instance deployments
- Add auth guards to registry endpoints in production (currently open for convenience)