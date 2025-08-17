"""
redis_store.py
==============

Клиент для работы с Redis. Используется для временного кэширования данных
с ограниченным временем жизни (TTL). Агент Coordination сохраняет в Redis
статусы задач и расписание cron.
"""

from typing import Any, Optional
import os
import logging

try:
    import redis  # type: ignore
    REDIS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    redis = None  # type: ignore
    REDIS_AVAILABLE = False

from memory.in_memory_store import InMemoryStore

logger = logging.getLogger(__name__)

# Import retry decorator if available
try:
    from core.retry import sync_retry
    RETRY_AVAILABLE = True
except ImportError:
    RETRY_AVAILABLE = False
    # Dummy decorator if retry not available
    def sync_retry(config=None):
        def decorator(func):
            return func
        return decorator


class RedisStore:
    """Простейшая обёртка над redis-py."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
        use_fallback: bool = True,
    ) -> None:
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db or int(os.getenv("REDIS_DB", "0"))
        self._use_fallback = use_fallback
        self._is_using_fallback = False
        
        if REDIS_AVAILABLE:
            try:
                self.client = redis.Redis(host=self.host, port=self.port, db=self.db)
                # Проверяем подключение
                self.client.ping()
                logger.info(f"✅ Connected to Redis at {self.host}:{self.port}")
            except Exception as e:
                if self._use_fallback:
                    logger.warning(f"⚠️ Redis недоступен ({e}), используем in-memory fallback")
                    self._setup_fallback()
                else:
                    raise RuntimeError(f"Не удалось подключиться к Redis: {e}")
        else:
            if self._use_fallback:
                logger.warning("⚠️ redis-py не установлен, используем in-memory fallback")
                self._setup_fallback()
            else:
                raise RuntimeError(
                    "Для работы RedisStore требуется библиотека redis-py. Установите её: pip install redis"
                )
    
    def _setup_fallback(self):
        """Настройка in-memory fallback."""
        self._is_using_fallback = True
        fallback = InMemoryStore()
        self.client = fallback.client

    @sync_retry(config="redis")
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Сохранить значение в Redis с TTL (в секундах)."""
        self.client.setex(name=key, time=ttl, value=value)

    @sync_retry(config="redis")
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
