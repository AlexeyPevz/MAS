# Дублирующиеся эндпоинты в main.py

## Эндпоинты, которые нужно удалить из main.py (уже есть в роутерах):

### Auth (routes_auth.py)
- POST /api/v1/auth/token (строки 1309-1338)
- POST /api/v1/auth/refresh (строки 1341-1366)
- POST /api/v1/auth/logout (строки 1369-1374)

### Voice (routes_voice.py)
- POST /api/v1/voice/stt (строка 460)
- POST /api/v1/voice/tts (строка 483)
- POST /api/v1/voice/chat (строка 509)

### Cache (routes_cache.py)
- GET /api/v1/cache/stats (строка 833)
- POST /api/v1/cache/clear (строка 863)

### Chat (routes_chat.py)
- POST /api/v1/chat/message (строка 570) - уже есть в routes_chat.py

### Registry (routes_registry.py)
- GET /api/v1/registry/tools (строка 992)
- GET /api/v1/registry/workflows (строка 997)
- GET /api/v1/registry/apps (строка 1002)
- POST /api/v1/registry/tools/{name}/rollback (строка 1032)
- POST /api/v1/registry/workflows/{key}/rollback (строка 1048)
- POST /api/v1/registry/apps/{key}/rollback (строка 1064)

### Misc (routes_misc.py)
- GET /api/v1/projects (строка 940)
- GET /api/v1/logs (строка 967)

### Federation (routes_federation.py)
- GET /api/v1/federation/status (строка 1268)
- POST /api/v1/federation/join (строка 1274)
- POST /api/v1/federation/sync (строка 1281)
- POST /federation/receive_knowledge (строка 1288)
- POST /federation/request_knowledge (строка 1295)

## Эндпоинты, которые остаются в main.py (не перенесены в роутеры):

### Core endpoints
- GET / (строка 405)
- GET /health (строка 414)
- GET /app (строка 345) - статические файлы
- GET /metrics (строка 894) - Prometheus метрики

### Chat endpoints (не перенесенные)
- POST /api/v1/chat/simple (строка 547)
- POST /api/v1/chat (строка 565)
- GET /api/v1/chat/history (строка 745)

### Other endpoints
- GET /api/v1/metrics/dashboard (строка 768) - отличается от routes_metrics.py
- GET /api/v1/voice/stats (строка 799)
- GET /api/v1/agents/status (строка 915)
- GET /api/v1/agents/profiles (строка 1204)
- GET /api/v1/studio/logs (строка 1163)
- GET /api/v1/visualization/flows (строка 1209)

### WebSocket endpoints
- WS /ws (строка 1099)
- WS /ws/visualization (строка 1214)

### Registry endpoints (не перенесенные)
- GET /api/v1/registry/instances (строка 1007)
- GET /api/v1/registry/tools/{name}/versions (строка 1012)
- GET /api/v1/registry/workflows/{key}/versions (строка 1017)
- GET /api/v1/registry/apps/{key}/versions (строка 1022)
- GET /api/v1/registry/instances/{key}/versions (строка 1027)
- POST /api/v1/registry/instances/{key}/rollback (строка 1080)

## Рекомендации:

1. Удалить все дублирующиеся эндпоинты из main.py
2. Перенести оставшиеся эндпоинты в соответствующие роутеры:
   - Chat endpoints → routes_chat.py
   - Agent endpoints → создать routes_agents.py
   - Studio/Visualization → создать routes_studio.py
   - WebSocket → создать routes_websocket.py
3. Оставить в main.py только:
   - Инициализацию приложения
   - Подключение роутеров
   - Middleware
   - Core endpoints (/, /health, /metrics)