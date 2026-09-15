from unittest.mock import MagicMock

from datapulse.raw_tables import (
    MIGRATIONS_DIR,
    apply_raw_support_tickets_table,
)


def test_raw_support_tickets_migration_exists() -> None:
    migration_path = MIGRATIONS_DIR / "008_create_raw_support_tickets_table.sql"
    assert migration_path.is_file()


def test_raw_support_tickets_migration_contains_expected_columns() -> None:
    migration_path = MIGRATIONS_DIR / "008_create_raw_support_tickets_table.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    expected_columns = [
        "raw_record_id BIGINT GENERATED ALWAYS AS IDENTITY",
        "ticket_id TEXT",
        "customer_id TEXT",
        "ticket_created_at TEXT",
        "ticket_updated_at TEXT",
        "ticket_category TEXT",
        "priority TEXT",
        "ticket_status TEXT",
        "resolution_channel TEXT",
        "assigned_team TEXT",
        "resolution_time_hours TEXT",
        "customer_satisfaction_score TEXT",
    ]

    for column_definition in expected_columns:
        assert column_definition in migration_sql


def test_apply_raw_support_tickets_table_executes_migration() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    apply_raw_support_tickets_table(engine)

    connection.execute.assert_called_once()
