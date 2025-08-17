"""
Root-MAS API Server
Единый API для всех клиентов: PWA, Telegram Bot, Mini App
"""
import os
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Import modular components
from .lifecycle import lifespan
from .middleware import setup_middleware
from .routers import register_routers
from config.settings import API_PORT, API_HOST, ENVIRONMENT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Root-MAS API",
    description="Multi-Agent System API with AutoGen 0.5+",
    version="0.1.0",
    lifespan=lifespan
)

# Setup middleware
setup_middleware(app)

# Register all routers
register_routers(app)

# Mount static files for PWA if directory exists
pwa_dir = Path(__file__).parent.parent / "pwa" / "dist"
if pwa_dir.exists():
    app.mount("/app", StaticFiles(directory=str(pwa_dir), html=True), name="pwa")
    logger.info(f"✅ PWA mounted at /app from {pwa_dir}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return JSONResponse({
        "name": "Root-MAS API",
        "version": "0.1.0",
        "status": "operational",
        "environment": ENVIRONMENT,
        "endpoints": {
            "api_docs": "/docs",
            "api_redoc": "/redoc",
            "health": "/health",
            "metrics": "/api/v1/metrics",
            "chat": "/api/v1/chat",
            "agents": "/api/v1/agents",
            "auth": "/api/v1/auth"
        },
        "features": {
            "multi_agent_system": True,
            "autogen_version": "0.5+",
            "voice_support": bool(os.getenv("YANDEX_API_KEY")),
            "telegram_bot": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "federation": bool(os.getenv("FEDERATION_ENABLED", "false").lower() == "true")
        }
    })

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check MAS integration
        mas_status = "healthy" if hasattr(app.state, 'mas_integration') else "not_initialized"
        
        # Check database connections
        db_status = {}
        if hasattr(app.state, 'db'):
            from core.database import db_manager
            db_health = await db_manager.health_check()
            db_status = db_health
        else:
            db_status = {"redis": "not_initialized", "postgres": "not_initialized"}
        
        # Overall status
        all_healthy = (
            mas_status == "healthy" and 
            all("healthy" in status for status in db_status.values())
        )
        
        return JSONResponse({
            "status": "healthy" if all_healthy else "degraded",
            "services": {
                "api": "healthy",
                "mas": mas_status,
                **db_status
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Development runner
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 Starting API server on {API_HOST}:{API_PORT}")
    
    uvicorn.run(
        "api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=ENVIRONMENT == "development",
        log_level="info"
    )