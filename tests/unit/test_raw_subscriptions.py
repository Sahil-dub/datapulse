from unittest.mock import MagicMock

from datapulse.raw_tables import (
    MIGRATIONS_DIR,
    apply_raw_subscriptions_table,
)


def test_raw_subscriptions_migration_exists() -> None:
    migration_path = MIGRATIONS_DIR / "007_create_raw_subscriptions_table.sql"
    assert migration_path.is_file()


def test_raw_subscriptions_migration_contains_expected_columns() -> None:
    migration_path = MIGRATIONS_DIR / "007_create_raw_subscriptions_table.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    expected_columns = [
        "raw_record_id BIGINT GENERATED ALWAYS AS IDENTITY",
        "subscription_id TEXT",
        "customer_id TEXT",
        "plan_type TEXT",
        "subscription_status TEXT",
        "billing_frequency TEXT",
        "start_date TEXT",
        "end_date TEXT",
        "monthly_fee TEXT",
        "auto_renew TEXT",
        "source_updated_at TEXT",
    ]

    for column_definition in expected_columns:
        assert column_definition in migration_sql


def test_apply_raw_subscriptions_table_executes_migration() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    apply_raw_subscriptions_table(engine)

    connection.execute.assert_called_once()
