"""
Central configuration settings for Root-MAS
"""
import os
from typing import Optional
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_PATH", BASE_DIR / "data"))
LOGS_DIR = Path(os.getenv("LOGS_PATH", BASE_DIR / "logs"))

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG = ENVIRONMENT == "development"
RUN_MODE = os.getenv("RUN_MODE", "full")  # full, api, mas

# API Server
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_BASE_URL = f"http://localhost:{API_PORT}"

# Security
SECRET_KEY = os.getenv("MAS_SECRET_KEY", "")  # Will be auto-generated if empty
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# LLM Providers
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_STREAMING = os.getenv("TELEGRAM_STREAMING", "true").lower() == "true"

# Voice (Yandex SpeechKit)
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")

# Databases
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "rootmas")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rootmas_secure_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "rootmas")

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8001"))

# Rate Limiting
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_MAX_MB = int(os.getenv("LOG_FILE_MAX_MB", "100"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# Monitoring
PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9090"))

# Federation
FEDERATION_ENABLED = os.getenv("FEDERATION_ENABLED", "false").lower() == "true"
FEDERATION_NODE_ID = os.getenv("FEDERATION_NODE_ID", "")

# External services
N8N_ENABLED = os.getenv("N8N_ENABLED", "false").lower() == "true"
N8N_URL = os.getenv("N8N_URL", "http://localhost:5678")
N8N_USER = os.getenv("N8N_USER", "admin")
N8N_PASSWORD = os.getenv("N8N_PASSWORD", "admin")

AUTOGEN_STUDIO_URL = os.getenv("AUTOGEN_STUDIO_URL", "")

# Timeouts
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))
MAX_CONVERSATION_LENGTH = int(os.getenv("MAX_CONVERSATION_LENGTH", "50"))

def validate_required_settings():
    """Validate that all required settings are present"""
    errors = []
    
    if not OPENROUTER_API_KEY:
        errors.append("OPENROUTER_API_KEY is required")
    
    if ENVIRONMENT == "production":
        if not SECRET_KEY:
            errors.append("MAS_SECRET_KEY should be set in production")
        if not ADMIN_SECRET:
            errors.append("ADMIN_SECRET is required in production")
    
    return errors

def get_database_url(driver: str = "postgresql") -> str:
    """Get database connection URL"""
    if driver == "postgresql":
        return f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    elif driver == "redis":
        return f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    else:
        raise ValueError(f"Unknown database driver: {driver}")