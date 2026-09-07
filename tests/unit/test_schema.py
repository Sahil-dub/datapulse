from datapulse.schema import MIGRATIONS_DIR


def test_raw_schema_migration_exists() -> None:
    migration_path = MIGRATIONS_DIR / "001_create_raw_schema.sql"

    assert migration_path.is_file()


def test_raw_schema_migration_is_utf8_and_creates_raw_schema() -> None:
    migration_path = MIGRATIONS_DIR / "001_create_raw_schema.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    assert "CREATE SCHEMA IF NOT EXISTS raw;" in migration_sql


def test_metadata_schema_migration_exists() -> None:
    migration_path = MIGRATIONS_DIR / "002_create_metadata_schema.sql"

    assert migration_path.is_file()


def test_metadata_schema_migration_is_utf8_and_creates_metadata_schema() -> None:
    migration_path = MIGRATIONS_DIR / "002_create_metadata_schema.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    assert "CREATE SCHEMA IF NOT EXISTS metadata;" in migration_sql
