"""
postgres_store.py
=================

Клиент для работы с базой данных PostgreSQL. Используется для хранения
задач, статуса инстансов и другой постоянной информации. В данной
заготовке реализован простой интерфейс для подключения и выполнения
SQL‑запросов. Для полноценной работы необходимо создать таблицы и
предоставить соответствующие SQL‑скрипты.
"""

from typing import Any, Iterable, Optional
import os

try:
    import psycopg2  # type: ignore
    from psycopg2.extras import RealDictCursor  # type: ignore
except ImportError:
    psycopg2 = None  # type: ignore


class PostgresStore:
    def __init__(self, host: str = None, port: int = None, dbname: str = None, user: str = None, password: str = None):
        if psycopg2 is None:
            raise RuntimeError("Для работы PostgresStore требуется библиотека psycopg2. Установите её: pip install psycopg2-binary")
        # Используем параметры из переменных окружения, если они не переданы явно
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

    def execute(self, query: str, params: Optional[Iterable[Any]] = None) -> Any:
        """Выполнить SQL‑запрос (INSERT/UPDATE/DELETE)."""
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            self.conn.commit()
            return cur.rowcount

    def fetch(self, query: str, params: Optional[Iterable[Any]] = None) -> Any:
        """Выполнить SELECT‑запрос и вернуть все результаты."""
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def close(self) -> None:
        self.conn.close()
