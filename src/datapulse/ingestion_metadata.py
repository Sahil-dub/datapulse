from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from datapulse.ingestion_contract import IngestionRequest

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "sql" / "migrations"


class IngestionMetadataError(RuntimeError):
    """Raised when ingestion metadata operations fail."""


class IngestionSourceStateError(IngestionMetadataError):
    """Raised when an ingestion source has an invalid lifecycle transition."""


def apply_ingestion_sources_table(engine: Engine) -> None:
    """Create the ingestion sources metadata table if it does not exist."""
    migration_path = MIGRATIONS_DIR / "011_create_ingestion_sources_table.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(text(migration_sql))


def apply_ingestion_source_row_counts(engine: Engine) -> None:
    """Add row-count tracking columns to the ingestion sources table."""
    migration_path = MIGRATIONS_DIR / "012_add_ingestion_source_row_counts.sql"
    migration_sql = migration_path.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(text(migration_sql))


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

    return int(ingestion_run_id)


def start_ingestion_source(
    engine: Engine,
    ingestion_run_id: int,
    request: IngestionRequest,
) -> int:
    """Create a PENDING ingestion source and return its generated ID."""
    if not request.source_name:
        raise IngestionMetadataError("source_name must not be empty.")

    started_at = datetime.now(UTC)

    query = text(
        """
        INSERT INTO metadata.ingestion_sources (
            ingestion_run_id,
            source_name,
            source_file_name,
            source_file_path,
            source_status,
            started_at
        )
        VALUES (
            :ingestion_run_id,
            :source_name,
            :source_file_name,
            :source_file_path,
            'PENDING',
            :started_at
        )
        RETURNING ingestion_source_id
        """
    )

    try:
        with engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "ingestion_run_id": ingestion_run_id,
                    "source_name": request.source_name,
                    "source_file_name": request.source_file_path.name,
                    "source_file_path": str(request.source_file_path),
                    "started_at": started_at,
                },
            )
            ingestion_source_id = result.scalar_one()
    except SQLAlchemyError as exc:
        raise IngestionMetadataError(
            f"{request.source_name}: failed to start ingestion source."
        ) from exc

    return int(ingestion_source_id)


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


def complete_ingestion_source(
    engine: Engine,
    ingestion_source_id: int,
    rows_read: int,
    rows_loaded: int,
) -> None:
    """Mark a PENDING ingestion source as successfully loaded."""
    finished_at = datetime.now(UTC)

    query = text(
        """
        UPDATE metadata.ingestion_sources
        SET
            source_status = 'SUCCESS',
            rows_read = :rows_read,
            rows_loaded = :rows_loaded,
            finished_at = :finished_at,
            error_message = NULL
        WHERE ingestion_source_id = :ingestion_source_id
          AND source_status = 'PENDING'
        """
    )

    try:
        with engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "ingestion_source_id": ingestion_source_id,
                    "rows_read": rows_read,
                    "rows_loaded": rows_loaded,
                    "finished_at": finished_at,
                },
            )
    except SQLAlchemyError as exc:
        raise IngestionMetadataError(
            f"Failed to complete ingestion source {ingestion_source_id}."
        ) from exc

    if result.rowcount != 1:
        raise IngestionSourceStateError(
            f"Ingestion source {ingestion_source_id} is not in PENDING state."
        )


def fail_ingestion_source(
    engine: Engine,
    ingestion_source_id: int,
    rows_read: int,
    rows_loaded: int,
    error_message: str,
) -> None:
    """Mark a PENDING ingestion source as failed."""
    finished_at = datetime.now(UTC)

    query = text(
        """
        UPDATE metadata.ingestion_sources
        SET
            source_status = 'FAILED',
            rows_read = :rows_read,
            rows_loaded = :rows_loaded,
            finished_at = :finished_at,
            error_message = :error_message
        WHERE ingestion_source_id = :ingestion_source_id
          AND source_status = 'PENDING'
        """
    )

    try:
        with engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "ingestion_source_id": ingestion_source_id,
                    "rows_read": rows_read,
                    "rows_loaded": rows_loaded,
                    "finished_at": finished_at,
                    "error_message": error_message,
                },
            )
    except SQLAlchemyError as exc:
        raise IngestionMetadataError(
            f"Failed to mark ingestion source {ingestion_source_id} as failed."
        ) from exc

    if result.rowcount != 1:
        raise IngestionSourceStateError(
            f"Ingestion source {ingestion_source_id} is not in PENDING state."
        )
