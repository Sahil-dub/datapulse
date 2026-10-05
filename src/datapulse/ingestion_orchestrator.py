from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import Engine

from datapulse.csv_validation import validate_csv_schema
from datapulse.db_loader import load_dataframe_to_raw_in_batches
from datapulse.file_reader import read_csv_file
from datapulse.ingestion_contract import IngestionRequest, IngestionResult, IngestionOutcome
from datapulse.ingestion_metadata import (
    complete_ingestion_run,
    complete_ingestion_source,
    start_ingestion_run,
    start_ingestion_source,
)
from datapulse.source_schema import get_source_columns

DEFAULT_BATCH_SIZE = 1_000


def ingest_source(
    engine: Engine,
    request: IngestionRequest,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> IngestionResult:
    """Run the successful single-source ingestion workflow."""
    ingestion_run_id = start_ingestion_run(
        engine,
        source_name=request.source_name,
    )

    ingestion_source_id = start_ingestion_source(
        engine,
        ingestion_run_id=ingestion_run_id,
        request=request,
    )

    dataframe = read_csv_file(request.source_file_path)
    rows_read = len(dataframe)

    validate_csv_schema(
        dataframe,
        expected_columns=get_source_columns(request.source_name),
        source_name=request.source_name,
    )

    rows_loaded = load_dataframe_to_raw_in_batches(
        engine,
        dataframe,
        source_name=request.source_name,
        batch_size=batch_size,
    )

    complete_ingestion_source(
        engine,
        ingestion_source_id=ingestion_source_id,
        rows_read=rows_read,
        rows_loaded=rows_loaded,
    )

    complete_ingestion_run(
        engine,
        ingestion_run_id=ingestion_run_id,
        rows_read=rows_read,
        rows_loaded=rows_loaded,
    )

    return IngestionResult(
        ingestion_run_id=ingestion_run_id,
        ingestion_source_id=ingestion_source_id,
        source_name=request.source_name,
        source_file_path=Path(request.source_file_path),
        outcome=IngestionOutcome.SUCCESS,
        rows_read=rows_read,
        rows_loaded=rows_loaded,
    )
