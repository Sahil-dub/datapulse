from unittest.mock import MagicMock

from datapulse.raw_tables import (
    MIGRATIONS_DIR,
    apply_raw_customers_table,
)


def test_raw_customers_migration_exists() -> None:
    migration_path = MIGRATIONS_DIR / "003_create_raw_customers_table.sql"

    assert migration_path.is_file()


def test_raw_customers_migration_contains_expected_columns() -> None:
    migration_path = MIGRATIONS_DIR / "003_create_raw_customers_table.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    expected_columns = [
        "raw_record_id BIGINT GENERATED ALWAYS AS IDENTITY",
        "customer_id TEXT",
        "first_name TEXT",
        "last_name TEXT",
        "email TEXT",
        "country TEXT",
        "signup_date TEXT",
        "customer_status TEXT",
        "acquisition_channel TEXT",
    ]

    for column_definition in expected_columns:
        assert column_definition in migration_sql


def test_apply_raw_customers_table_executes_migration() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    apply_raw_customers_table(engine)

    connection.execute.assert_called_once()
