from unittest.mock import MagicMock

from datapulse.raw_tables import (
    MIGRATIONS_DIR,
    apply_raw_payments_table,
)


def test_raw_payments_migration_exists() -> None:
    migration_path = MIGRATIONS_DIR / "006_create_raw_payments_table.sql"
    assert migration_path.is_file()


def test_raw_payments_migration_contains_expected_columns() -> None:
    migration_path = MIGRATIONS_DIR / "006_create_raw_payments_table.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    expected_columns = [
        "raw_record_id BIGINT GENERATED ALWAYS AS IDENTITY",
        "payment_id TEXT",
        "order_id TEXT",
        "payment_date TEXT",
        "payment_method TEXT",
        "payment_amount TEXT",
        "payment_status TEXT",
        "transaction_reference TEXT",
        "currency TEXT",
        "source_updated_at TEXT",
    ]

    for column_definition in expected_columns:
        assert column_definition in migration_sql


def test_apply_raw_payments_table_executes_migration() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    apply_raw_payments_table(engine)

    connection.execute.assert_called_once()
