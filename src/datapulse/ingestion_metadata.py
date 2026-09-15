from pathlib import Path

from sqlalchemy import Engine, text

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "sql" / "migrations"


def apply_ingestion_runs_table(engine: Engine) -> None:
    """Create the ingestion runs metadata table if it does not exist."""
    migration_path = MIGRATIONS_DIR / "010_create_ingestion_runs_table.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(text(migration_sql))
