"""
Router registration for the API
"""
import logging
from fastapi import FastAPI

# Import all routers
from .routes_chat import router as chat_router
from .routes_voice import router as voice_router
from .routes_metrics import router as metrics_router
from .routes_registry import router as registry_router
from .routes_auth import router as auth_router
from .routes_cache import router as cache_router
from .routes_federation import router as federation_router
from .routes_misc import router as misc_router
from .routes_agents import router as agents_router
from .routes_websocket import router as websocket_router
from .routes_studio import router as studio_router

logger = logging.getLogger(__name__)


def register_routers(app: FastAPI) -> None:
    """Register all API routers"""
    
    # Register routers with their prefixes already defined
    routers = [
        (chat_router, "Chat API"),
        (voice_router, "Voice API"),
        (metrics_router, "Metrics API"),
        (registry_router, "Registry API"),
        (auth_router, "Authentication API"),
        (cache_router, "Cache API"),
        (federation_router, "Federation API"),
        (misc_router, "Miscellaneous API"),
        (agents_router, "Agents API"),
        (websocket_router, "WebSocket API"),
        (studio_router, "Studio API"),
    ]
    
    for router, name in routers:
        app.include_router(router)
        logger.info(f"✅ Registered {name}")
    
    logger.info(f"✅ Total {len(routers)} routers registered")