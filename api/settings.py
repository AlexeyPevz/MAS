import os
from typing import List, Optional
from pydantic import BaseModel


class AppSettings(BaseModel):
    environment: str
    cors_origins: List[str]
    allow_credentials: bool
    trusted_hosts: Optional[List[str]] = None
    enforce_https: bool = False

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
        )


settings = AppSettings.from_env()