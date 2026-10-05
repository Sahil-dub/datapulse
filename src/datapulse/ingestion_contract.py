from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class IngestionOutcome(StrEnum):
    """Terminal outcome of a single-source ingestion workflow."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@dataclass(frozen=True)
class IngestionRequest:
    """Inputs required to ingest one source file."""

    source_name: str
    source_file_path: Path


@dataclass(frozen=True)
class IngestionResult:
    """Metadata returned by a completed single-source ingestion workflow."""

    ingestion_run_id: int
    ingestion_source_id: int
    source_name: str
    source_file_path: Path
    outcome: IngestionOutcome
    rows_read: int
    rows_loaded: int
    error_message: str | None = None
