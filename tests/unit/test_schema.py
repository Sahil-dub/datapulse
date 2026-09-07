from unittest.mock import MagicMock

import pytest

from datapulse.schema import (
    MIGRATIONS_DIR,
    DatabaseSchemaValidationError,
    validate_database_schemas,
)


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


def test_validate_database_schemas_passes_when_required_schemas_exist() -> None:
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value = [
        ("raw", "datapulse"),
        ("metadata", "datapulse"),
    ]

    validate_database_schemas(engine, expected_owner="datapulse")

    connection.execute.assert_called_once()


def test_validate_database_schemas_reports_missing_schemas() -> None:
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value = [("raw", "datapulse")]

    with pytest.raises(
        DatabaseSchemaValidationError,
        match="Required DataPulse database schemas are missing: metadata",
    ):
        validate_database_schemas(engine, expected_owner="datapulse")


def test_validate_database_schemas_reports_unexpected_owner() -> None:
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value = [
        ("raw", "datapulse"),
        ("metadata", "wrong_owner"),
    ]

    with pytest.raises(
        DatabaseSchemaValidationError,
        match="DataPulse database schemas have unexpected owners: metadata",
    ):
        validate_database_schemas(engine, expected_owner="datapulse")
