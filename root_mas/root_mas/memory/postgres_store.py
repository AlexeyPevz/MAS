"""
postgres_store.py
=================

Клиент для работы с базой данных PostgreSQL. Используется для хранения
задач, статуса инстансов и другой постоянной информации. Предоставляет
простые методы для выполнения SQL-запросов и чтения данных.
"""

from typing import Any, Iterable, Optional
import os

try:
    import psycopg2  # type: ignore
    from psycopg2.extras import RealDictCursor  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    psycopg2 = None  # type: ignore


class PostgresStore:
    """Обёртка над psycopg2 для простых операций."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        dbname: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        if psycopg2 is None:
            raise RuntimeError(
                "Для работы PostgresStore требуется библиотека psycopg2. Установите её: pip install psycopg2-binary"
            )
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        self.dbname = dbname or os.getenv("POSTGRES_DB", "mas")
        self.user = user or os.getenv("POSTGRES_USER", "mas")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "maspass")
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            cursor_factory=RealDictCursor,
        )

    def execute(self, query: str, params: Optional[Iterable[Any]] = None) -> int:
        """Выполнить запрос INSERT/UPDATE/DELETE."""
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            self.conn.commit()
            return cur.rowcount

    def fetch(self, query: str, params: Optional[Iterable[Any]] = None) -> list[dict]:
        """Выполнить SELECT-запрос и вернуть результаты."""
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def execute_script(self, script: str) -> None:
        """Выполнить многострочный SQL-скрипт."""
        with self.conn.cursor() as cur:
            cur.execute(script)
            self.conn.commit()

    def close(self) -> None:
        self.conn.close()
