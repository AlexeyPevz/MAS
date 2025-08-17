import os
from typing import List, Optional
from pydantic import BaseModel


class AppSettings(BaseModel):
    environment: str
    cors_origins: List[str]
    allow_credentials: bool
    trusted_hosts: Optional[List[str]] = None
    enforce_https: bool = False
    # Extended
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    data_path: str = "data"
    redis_host: str = "localhost"
    redis_port: int = 6379
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    @classmethod
    def from_env(cls) -> "AppSettings":
        env = os.getenv("ENVIRONMENT", "production")
        cors = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
        allow_credentials = env == "development"
        th = os.getenv("TRUSTED_HOSTS")
        trusted = th.split(",") if th else None
        enforce_https = os.getenv("ENFORCE_HTTPS", "false").lower() in {"1", "true", "yes"}
        return cls(
            environment=env,
            cors_origins=[c for c in cors.split(",") if c],
            allow_credentials=allow_credentials,
            trusted_hosts=trusted,
            enforce_https=enforce_https,
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
            data_path=os.getenv("DATA_PATH", "data"),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            chroma_host=os.getenv("CHROMA_HOST", "localhost"),
            chroma_port=int(os.getenv("CHROMA_PORT", "8000")),
        )


settings = AppSettings.from_env()