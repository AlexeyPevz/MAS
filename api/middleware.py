"""
API Middleware configuration
"""
import os
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from config.settings import ENVIRONMENT

logger = logging.getLogger(__name__)


def setup_middleware(app: FastAPI) -> None:
    """Setup all middleware for the application"""
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8080",
            "https://your-domain.com",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted Host Middleware (production only)
    if ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["your-domain.com", "*.your-domain.com"]
        )
        
        # HTTPS Redirect Middleware (production only)
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Custom request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"📨 {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate process time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        logger.info(f"✅ {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
        
        return response
    
    # Error handling middleware
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "type": "internal_error",
                "message": str(exc) if ENVIRONMENT == "development" else "An error occurred"
            }
        )
    
    logger.info("✅ Middleware configured")