"""
Application lifecycle management (startup/shutdown)
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import AsyncGenerator

from config.settings import REDIS_HOST, ENVIRONMENT, PROMETHEUS_ENABLED
from .integration import mas_integration
from memory.redis_store import RedisStore
from core.factory import ComponentFactory
from core.database import db_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Manage application lifecycle"""
    logger.info("🚀 Starting Root-MAS API Server...")
    
    # Startup
    try:
        # Initialize database connections with pools
        logger.info("🔧 Initializing database connections...")
        await db_manager.initialize()
        app.state.db = db_manager
        
        # Initialize Redis store (legacy compatibility)
        logger.info("🔧 Initializing Redis store...")
        store = RedisStore(use_fallback=True)
        app.state.store = store
        
        # Initialize MAS integration
        logger.info("🤖 Initializing MAS system...")
        await mas_integration.initialize()
        app.state.mas_integration = mas_integration
        
        # Initialize voice processor if configured
        if os.getenv("YANDEX_API_KEY"):
            try:
                logger.info("🎤 Initializing Voice Processor...")
                voice_processor = ComponentFactory.create(
                    "voice_processor",
                    os.getenv("YANDEX_API_KEY")
                )
                if voice_processor:
                    await voice_processor.initialize()
                    app.state.voice_processor = voice_processor
                    logger.info("✅ Voice Processor initialized")
            except Exception as e:
                logger.warning(f"⚠️ Voice Processor initialization failed: {e}")
        
        # Initialize monitoring if enabled
        if PROMETHEUS_ENABLED:
            logger.info("📊 Prometheus monitoring enabled")
            # Monitoring initialization would go here
        
        # Log startup info
        logger.info(f"🌍 Environment: {ENVIRONMENT}")
        logger.info(f"🗄️ Redis: {REDIS_HOST}")
        logger.info("✅ All systems initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    # Run application
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Root-MAS API Server...")
    
    try:
        # Cleanup MAS integration
        if hasattr(app.state, 'mas_integration'):
            await mas_integration.cleanup()
            logger.info("✅ MAS integration cleaned up")
        
        # Cleanup voice processor
        if hasattr(app.state, 'voice_processor'):
            await app.state.voice_processor.shutdown()
            logger.info("✅ Voice Processor shut down")
        
        # Cleanup component factory
        ComponentFactory.clear()
        logger.info("✅ Component factory cleared")
        
        # Close database connections
        if hasattr(app.state, 'db'):
            await db_manager.cleanup()
            logger.info("✅ Database connections closed")
        
        # Close Redis connections (legacy)
        if hasattr(app.state, 'store'):
            # RedisStore doesn't have explicit cleanup
            pass
        
        logger.info("✅ Shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")