from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from datapulse.ingestion_metadata import (
    IngestionMetadataError,
    apply_ingestion_sources_table,
    complete_ingestion_run,
    fail_ingestion_run,
    start_ingestion_run,
)


def test_start_ingestion_run_returns_generated_run_id() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    result = MagicMock()
    result.scalar_one.return_value = 42
    connection.execute.return_value = result

    ingestion_run_id = start_ingestion_run(
        engine,
        source_name="customers",
    )

    assert ingestion_run_id == 42
    engine.begin.assert_called_once()
    connection.execute.assert_called_once()


def test_start_ingestion_run_creates_running_run() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    result = MagicMock()
    result.scalar_one.return_value = 42
    connection.execute.return_value = result

    start_ingestion_run(
        engine,
        source_name="customers",
        rows_read=500,
    )

    parameters = connection.execute.call_args.args[1]

    assert parameters["source_name"] == "customers"
    assert parameters["rows_read"] == 500
    assert isinstance(parameters["started_at"], datetime)


def test_start_ingestion_run_rejects_empty_source() -> None:
    engine = MagicMock()

    with pytest.raises(
        IngestionMetadataError,
        match="source_name must not be empty",
    ):
        start_ingestion_run(engine, source_name="")


def test_start_ingestion_run_rejects_negative_rows() -> None:
    engine = MagicMock()

    with pytest.raises(
        IngestionMetadataError,
        match="rows_read must not be negative",
    ):
        start_ingestion_run(
            engine,
            source_name="customers",
            rows_read=-1,
        )

    engine.begin.assert_not_called()


def test_start_ingestion_run_wraps_database_error() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    original_error = SQLAlchemyError("database failure")
    connection.execute.side_effect = original_error

    with pytest.raises(
        IngestionMetadataError,
        match="customers: failed to start ingestion run",
    ) as exc_info:
        start_ingestion_run(
            engine,
            source_name="customers",
        )

    assert exc_info.value.__cause__ is original_error


def test_complete_ingestion_run_updates_success_state() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    result = MagicMock()
    result.rowcount = 1
    connection.execute.return_value = result

    complete_ingestion_run(
        engine,
        ingestion_run_id=42,
        rows_read=500,
        rows_loaded=495,
    )

    parameters = connection.execute.call_args.args[1]

    assert parameters["ingestion_run_id"] == 42
    assert parameters["rows_read"] == 500
    assert parameters["rows_loaded"] == 495
    assert isinstance(parameters["finished_at"], datetime)


def test_complete_ingestion_run_rejects_non_running_run() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    result = MagicMock()
    result.rowcount = 0
    connection.execute.return_value = result

    with pytest.raises(
        IngestionMetadataError,
        match="cannot be completed",
    ):
        complete_ingestion_run(
            engine,
            ingestion_run_id=999,
            rows_read=10,
            rows_loaded=10,
        )


def test_complete_ingestion_run_rejects_negative_counts() -> None:
    engine = MagicMock()

    with pytest.raises(
        IngestionMetadataError,
        match="rows_read must not be negative",
    ):
        complete_ingestion_run(
            engine,
            ingestion_run_id=42,
            rows_read=-1,
            rows_loaded=10,
        )

    engine.begin.assert_not_called()

    with pytest.raises(
        IngestionMetadataError,
        match="rows_loaded must not be negative",
    ):
        complete_ingestion_run(
            engine,
            ingestion_run_id=42,
            rows_read=10,
            rows_loaded=-1,
        )

    engine.begin.assert_not_called()


def test_complete_ingestion_run_wraps_database_error() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    original_error = SQLAlchemyError("database failure")
    connection.execute.side_effect = original_error

    with pytest.raises(
        IngestionMetadataError,
        match="failed to complete ingestion run",
    ) as exc_info:
        complete_ingestion_run(
            engine,
            ingestion_run_id=42,
            rows_read=10,
            rows_loaded=10,
        )

    assert exc_info.value.__cause__ is original_error


def test_fail_ingestion_run_updates_failed_state() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    result = MagicMock()
    result.rowcount = 1
    connection.execute.return_value = result

    fail_ingestion_run(
        engine,
        ingestion_run_id=42,
        rows_read=500,
        rows_loaded=250,
        error_message="Database connection failed.",
    )

    parameters = connection.execute.call_args.args[1]

    assert parameters["ingestion_run_id"] == 42
    assert parameters["rows_read"] == 500
    assert parameters["rows_loaded"] == 250
    assert parameters["error_message"] == "Database connection failed."
    assert isinstance(parameters["finished_at"], datetime)


def test_fail_ingestion_run_rejects_non_running_run() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    result = MagicMock()
    result.rowcount = 0
    connection.execute.return_value = result

    with pytest.raises(
        IngestionMetadataError,
        match="cannot be marked as failed",
    ):
        fail_ingestion_run(
            engine,
            ingestion_run_id=999,
            rows_read=10,
            rows_loaded=0,
            error_message="Test failure.",
        )


def test_fail_ingestion_run_rejects_empty_error_message() -> None:
    engine = MagicMock()

    with pytest.raises(
        IngestionMetadataError,
        match="error_message must not be empty",
    ):
        fail_ingestion_run(
            engine,
            ingestion_run_id=42,
            rows_read=10,
            rows_loaded=0,
            error_message="",
        )

    engine.begin.assert_not_called()


def test_fail_ingestion_run_wraps_database_error() -> None:
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    original_error = SQLAlchemyError("database failure")
    connection.execute.side_effect = original_error

    with pytest.raises(
        IngestionMetadataError,
        match="failed to mark ingestion run as failed",
    ) as exc_info:
        fail_ingestion_run(
            engine,
            ingestion_run_id=42,
            rows_read=10,
            rows_loaded=0,
            error_message="Database failure.",
        )

    assert exc_info.value.__cause__ is original_error


def test_ingestion_sources_migration_exists() -> None:
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "sql"
        / "migrations"
        / "011_create_ingestion_sources_table.sql"
    )

    assert migration_path.exists()


def test_apply_ingestion_sources_table_executes_migration() -> None:
    engine = MagicMock()

    apply_ingestion_sources_table(engine)

    engine.begin.assert_called_once()

    connection = engine.begin.return_value.__enter__.return_value
    connection.execute.assert_called_once()


def test_ingestion_sources_migration_contains_expected_contract() -> None:
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "sql"
        / "migrations"
        / "011_create_ingestion_sources_table.sql"
    )

    migration_sql = migration_path.read_text(encoding="utf-8")

    expected_fragments = (
        "CREATE TABLE IF NOT EXISTS metadata.ingestion_sources",
        "ingestion_source_id BIGINT GENERATED ALWAYS AS IDENTITY",
        "ingestion_run_id BIGINT NOT NULL",
        "source_name TEXT NOT NULL",
        "source_file_name TEXT NOT NULL",
        "source_file_path TEXT NOT NULL",
        "source_status TEXT NOT NULL DEFAULT 'PENDING'",
        "started_at TIMESTAMPTZ NOT NULL",
        "finished_at TIMESTAMPTZ",
        "error_message TEXT",
        "pk_ingestion_sources",
        "fk_ingestion_sources_ingestion_runs",
        "uq_ingestion_sources_run_file",
        "ck_ingestion_sources_status",
        "ck_ingestion_sources_finished_at",
    )

    for fragment in expected_fragments:
        assert fragment in migration_sql
