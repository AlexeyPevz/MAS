"""
redis_store.py
==============

Клиент для работы с Redis. Используется для временного кэширования данных
с ограниченным временем жизни (TTL). Агент Coordination сохраняет в Redis
статусы задач и расписание cron.
"""

from typing import Any, Optional
import os

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    redis = None  # type: ignore


class RedisStore:
    """Простейшая обёртка над redis-py."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
    ) -> None:
        if redis is None:
            raise RuntimeError(
                "Для работы RedisStore требуется библиотека redis-py. Установите её: pip install redis"
            )
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db or int(os.getenv("REDIS_DB", "0"))
        self.client = redis.Redis(host=self.host, port=self.port, db=self.db)

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Сохранить значение в Redis с TTL (в секундах)."""
        self.client.setex(name=key, time=ttl, value=value)

    def get(self, key: str) -> Optional[Any]:
        """Получить значение из Redis, если оно существует."""
        return self.client.get(key)

    def delete(self, key: str) -> None:
        """Удалить запись из Redis."""
        self.client.delete(key)

    def exists(self, key: str) -> bool:
        """Проверить наличие ключа."""
        return bool(self.client.exists(key))

    def keys(self, pattern: str = "*") -> list[str]:
        """Получить список ключей по шаблону."""
        return [k.decode("utf-8") if isinstance(k, bytes) else k for k in self.client.keys(pattern)]
