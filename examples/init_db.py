from pathlib import Path
from memory.postgres_store import PostgresStore


def main() -> None:
    """Apply SQL migrations to initialise the PostgreSQL database."""
    store = PostgresStore()
    migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    script_path = migrations_dir / "001_init.sql"
    with script_path.open("r", encoding="utf-8") as f:
        store.execute_script(f.read())
    store.close()
    print("Database initialised")


if __name__ == "__main__":
    main()
