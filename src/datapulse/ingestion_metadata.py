from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "sql" / "migrations"


def apply_ingestion_sources_table(engine: Engine) -> None:
    """Create the ingestion sources metadata table if it does not exist."""
    migration_path = MIGRATIONS_DIR / "011_create_ingestion_sources_table.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(text(migration_sql))


class IngestionMetadataError(RuntimeError):
    """Raised when ingestion run metadata cannot be updated."""


def start_ingestion_run(
    engine: Engine,
    source_name: str,
    rows_read: int = 0,
) -> int:
    """Create a new ingestion run in RUNNING state and return its ID."""
    if not source_name:
        raise IngestionMetadataError("source_name must not be empty.")

    if rows_read < 0:
        raise IngestionMetadataError("rows_read must not be negative.")

    started_at = datetime.now(UTC)

    query = text(
        """
        INSERT INTO metadata.ingestion_runs (
            source_name,
            started_at,
            status,
            rows_read,
            rows_loaded
        )
        VALUES (
            :source_name,
            :started_at,
            'RUNNING',
            :rows_read,
            0
        )
        RETURNING ingestion_run_id
        """
    )

    try:
        with engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "source_name": source_name,
                    "started_at": started_at,
                    "rows_read": rows_read,
                },
            )
            ingestion_run_id = result.scalar_one()
    except SQLAlchemyError as exc:
        raise IngestionMetadataError(f"{source_name}: failed to start ingestion run.") from exc

    return ingestion_run_id


def complete_ingestion_run(
    engine: Engine,
    ingestion_run_id: int,
    rows_read: int,
    rows_loaded: int,
) -> None:
    """Mark a RUNNING ingestion run as successfully completed."""
    if rows_read < 0:
        raise IngestionMetadataError("rows_read must not be negative.")

    if rows_loaded < 0:
        raise IngestionMetadataError("rows_loaded must not be negative.")

    finished_at = datetime.now(UTC)

    query = text(
        """
        UPDATE metadata.ingestion_runs
        SET
            status = 'SUCCESS',
            rows_read = :rows_read,
            rows_loaded = :rows_loaded,
            finished_at = :finished_at
        WHERE ingestion_run_id = :ingestion_run_id
          AND status = 'RUNNING'
        """
    )

    try:
        with engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "ingestion_run_id": ingestion_run_id,
                    "rows_read": rows_read,
                    "rows_loaded": rows_loaded,
                    "finished_at": finished_at,
                },
            )

            if result.rowcount != 1:
                raise IngestionMetadataError(
                    "Ingestion run cannot be completed because it does not "
                    "exist or is not in RUNNING state."
                )

    except IngestionMetadataError:
        raise
    except SQLAlchemyError as exc:
        raise IngestionMetadataError(
            f"Ingestion run {ingestion_run_id}: failed to complete ingestion run."
        ) from exc


def fail_ingestion_run(
    engine: Engine,
    ingestion_run_id: int,
    rows_read: int,
    rows_loaded: int,
    error_message: str,
) -> None:
    """Mark a RUNNING ingestion run as failed."""
    if rows_read < 0:
        raise IngestionMetadataError("rows_read must not be negative.")

    if rows_loaded < 0:
        raise IngestionMetadataError("rows_loaded must not be negative.")

    if not error_message:
        raise IngestionMetadataError("error_message must not be empty.")

    finished_at = datetime.now(UTC)

    query = text(
        """
        UPDATE metadata.ingestion_runs
        SET
            status = 'FAILED',
            rows_read = :rows_read,
            rows_loaded = :rows_loaded,
            finished_at = :finished_at,
            error_message = :error_message
        WHERE ingestion_run_id = :ingestion_run_id
          AND status = 'RUNNING'
        """
    )

    try:
        with engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "ingestion_run_id": ingestion_run_id,
                    "rows_read": rows_read,
                    "rows_loaded": rows_loaded,
                    "finished_at": finished_at,
                    "error_message": error_message,
                },
            )

            if result.rowcount != 1:
                raise IngestionMetadataError(
                    "Ingestion run cannot be marked as failed because it "
                    "does not exist or is not in RUNNING state."
                )

    except IngestionMetadataError:
        raise
    except SQLAlchemyError as exc:
        raise IngestionMetadataError(
            f"Ingestion run {ingestion_run_id}: failed to mark ingestion run as failed."
        ) from exc


def apply_ingestion_source_row_counts(engine: Engine) -> None:
    """Add row-count tracking columns to the ingestion sources table."""
    migration_path = MIGRATIONS_DIR / "012_add_ingestion_source_row_counts.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(text(migration_sql))
