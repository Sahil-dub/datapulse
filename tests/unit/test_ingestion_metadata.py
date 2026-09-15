from pathlib import Path
from unittest.mock import MagicMock

from datapulse.ingestion_metadata import apply_ingestion_runs_table


def test_ingestion_runs_migration_exists() -> None:
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "sql"
        / "migrations"
        / "010_create_ingestion_runs_table.sql"
    )

    assert migration_path.exists()


def test_apply_ingestion_runs_table_executes_migration() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    apply_ingestion_runs_table(engine)

    engine.begin.assert_called_once()
    connection.execute.assert_called_once()


def test_ingestion_runs_migration_contains_expected_contract() -> None:
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "sql"
        / "migrations"
        / "010_create_ingestion_runs_table.sql"
    )

    migration_sql = migration_path.read_text(encoding="utf-8")

    expected_fragments = (
        "CREATE TABLE IF NOT EXISTS metadata.ingestion_runs",
        "ingestion_run_id BIGINT GENERATED ALWAYS AS IDENTITY",
        "source_name TEXT NOT NULL",
        "started_at TIMESTAMPTZ NOT NULL",
        "finished_at TIMESTAMPTZ",
        "status TEXT NOT NULL",
        "rows_read BIGINT NOT NULL DEFAULT 0",
        "rows_loaded BIGINT NOT NULL DEFAULT 0",
        "error_message TEXT",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "pk_ingestion_runs",
        "ck_ingestion_runs_status",
        "ck_ingestion_runs_rows_read",
        "ck_ingestion_runs_rows_loaded",
        "ck_ingestion_runs_finished_at",
    )

    for fragment in expected_fragments:
        assert fragment in migration_sql
