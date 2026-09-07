from pathlib import Path

from sqlalchemy import Engine, text

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "sql" / "migrations"


def apply_raw_customers_table(engine: Engine) -> None:
    """Create the raw customers table if it does not already exist."""
    migration_path = MIGRATIONS_DIR / "003_create_raw_customers_table.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(text(migration_sql))
