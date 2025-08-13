"""
In-Memory Store
==============

In-memory fallback для Redis. Используется когда Redis недоступен.
Поддерживает TTL и основные операции.
"""

import time
from typing import Any, Optional, Dict, Tuple
from threading import Lock


class InMemoryStore:
    """In-memory хранилище с поддержкой TTL как fallback для Redis."""
    
    def __init__(self, host: str | None = None, port: int | None = None, db: int | None = None):
        # Игнорируем параметры подключения, так как это in-memory
        self._data: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry_time)
        self._lock = Lock()
        self.host = "memory"
        self.port = 0
        self.db = 0
        
    def _cleanup_expired(self):
        """Удаляет истекшие записи."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._data.items()
            if expiry and expiry < current_time
        ]
        for key in expired_keys:
            del self._data[key]
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Сохранить значение с TTL (в секундах)."""
        with self._lock:
            expiry_time = time.time() + ttl if ttl > 0 else None
            self._data[key] = (value, expiry_time)
            self._cleanup_expired()
    
    def get(self, key: str) -> Optional[Any]:
        """Получить значение, если оно существует и не истекло."""
        with self._lock:
            self._cleanup_expired()
            if key in self._data:
                value, expiry = self._data[key]
                if expiry is None or expiry > time.time():
                    return value
                else:
                    del self._data[key]
            return None
    
    def delete(self, key: str) -> None:
        """Удалить запись."""
        with self._lock:
            self._data.pop(key, None)
    
    def exists(self, key: str) -> bool:
        """Проверить наличие ключа."""
        with self._lock:
            self._cleanup_expired()
            if key in self._data:
                _, expiry = self._data[key]
                if expiry is None or expiry > time.time():
                    return True
                else:
                    del self._data[key]
            return False
    
    def ping(self) -> bool:
        """Проверить доступность хранилища (всегда True для in-memory)."""
        return True
    
    def keys(self, pattern: str = "*") -> list:
        """Получить список ключей по паттерну."""
        with self._lock:
            self._cleanup_expired()
            # Простая реализация паттернов
            if pattern == "*":
                return list(self._data.keys())
            elif pattern.endswith("*"):
                prefix = pattern[:-1]
                return [k for k in self._data.keys() if k.startswith(prefix)]
            else:
                return [k for k in self._data.keys() if pattern in k]
    
    def flushdb(self) -> None:
        """Очистить всё хранилище."""
        with self._lock:
            self._data.clear()
    
    def ttl(self, key: str) -> int:
        """Получить оставшееся время жизни ключа в секундах."""
        with self._lock:
            if key in self._data:
                _, expiry = self._data[key]
                if expiry:
                    remaining = int(expiry - time.time())
                    return max(0, remaining)
                return -1  # Нет TTL
            return -2  # Ключ не существует
    
    def setex(self, name: str, time: int, value: Any) -> None:
        """Alias для set() для совместимости с redis-py."""
        self.set(name, value, time)
    
    @property
    def client(self):
        """Для совместимости с RedisStore."""
        return self