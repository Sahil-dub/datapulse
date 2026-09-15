from unittest.mock import MagicMock

from datapulse.raw_tables import (
    MIGRATIONS_DIR,
    apply_raw_web_events_table,
)


def test_raw_web_events_migration_exists() -> None:
    migration_path = MIGRATIONS_DIR / "009_create_raw_web_events_table.sql"
    assert migration_path.is_file()


def test_raw_web_events_migration_contains_expected_columns() -> None:
    migration_path = MIGRATIONS_DIR / "009_create_raw_web_events_table.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    expected_columns = [
        "raw_record_id BIGINT GENERATED ALWAYS AS IDENTITY",
        "event_id TEXT",
        "event_timestamp TEXT",
        "source_received_at TEXT",
        "session_id TEXT",
        "customer_id TEXT",
        "event_type TEXT",
        "page_type TEXT",
        "device_type TEXT",
        "traffic_source TEXT",
        "product_id TEXT",
        "order_id TEXT",
        "revenue_amount TEXT",
    ]

    for column_definition in expected_columns:
        assert column_definition in migration_sql


def test_apply_raw_web_events_table_executes_migration() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    apply_raw_web_events_table(engine)

    connection.execute.assert_called_once()
