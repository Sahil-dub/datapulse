from pathlib import Path

from sqlalchemy import Engine, text

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "sql" / "migrations"
EXPECTED_SCHEMAS = ("raw", "metadata")


class DatabaseSchemaValidationError(RuntimeError):
    """Raised when an expected DataPulse database schema is invalid."""


def apply_raw_schema(engine: Engine) -> None:
    """Create the raw PostgreSQL schema if it does not already exist."""
    migration_path = MIGRATIONS_DIR / "001_create_raw_schema.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(text(migration_sql))


def apply_metadata_schema(engine: Engine) -> None:
    """Create the metadata PostgreSQL schema if it does not already exist."""
    migration_path = MIGRATIONS_DIR / "002_create_metadata_schema.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(text(migration_sql))


def validate_database_schemas(
    engine: Engine,
    expected_owner: str,
) -> None:
    """Validate required DataPulse schemas and their ownership."""
    query = text(
        "SELECT schema_name, schema_owner "
        "FROM information_schema.schemata "
        "WHERE schema_name IN (:raw_schema, :metadata_schema)"
    )

    with engine.connect() as connection:
        existing_schemas = {
            row[0]: row[1]
            for row in connection.execute(
                query,
                {
                    "raw_schema": EXPECTED_SCHEMAS[0],
                    "metadata_schema": EXPECTED_SCHEMAS[1],
                },
            )
        }

    missing_schemas = set(EXPECTED_SCHEMAS) - existing_schemas.keys()
    if missing_schemas:
        missing = ", ".join(sorted(missing_schemas))
        raise DatabaseSchemaValidationError(
            f"Required DataPulse database schemas are missing: {missing}"
        )

    incorrectly_owned = {
        schema_name
        for schema_name, schema_owner in existing_schemas.items()
        if schema_owner != expected_owner
    }

    if incorrectly_owned:
        invalid = ", ".join(sorted(incorrectly_owned))
        raise DatabaseSchemaValidationError(
            f"DataPulse database schemas have unexpected owners: {invalid}"
        )
