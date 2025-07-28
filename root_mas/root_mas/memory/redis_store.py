"""
redis_store.py
==============

Клиент для работы с Redis. Используется для временного кэширования данных
с ограниченным временем жизни (TTL). Агент Coordination сохраняет в Redis
статусы задач и расписание cron.
"""

from typing import Any, Optional

try:
    import redis  # type: ignore
except ImportError:
    redis = None  # type: ignore


class RedisStore:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        if redis is None:
            raise RuntimeError("Для работы RedisStore требуется библиотека redis-py. Установите её: pip install redis")
        self.client = redis.Redis(host=host, port=port, db=db)

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Сохранить значение в Redis с TTL (в секундах)."""
        self.client.setex(key, ttl, value)

    def get(self, key: str) -> Optional[Any]:
        """Получить значение из Redis, если оно существует."""
        return self.client.get(key)

    def delete(self, key: str) -> None:
        """Удалить запись из Redis."""
        self.client.delete(key)
