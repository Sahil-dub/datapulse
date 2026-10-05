from pathlib import Path

import pytest

from datapulse.ingestion_contract import (
    IngestionOutcome,
    IngestionRequest,
    IngestionResult,
)


def test_ingestion_request_captures_source_name_and_path() -> None:
    request = IngestionRequest(
        source_name="customers",
        source_file_path=Path("data/generated/customers/customers.csv"),
    )

    assert request.source_name == "customers"
    assert request.source_file_path == Path("data/generated/customers/customers.csv")


def test_ingestion_request_is_immutable() -> None:
    request = IngestionRequest(
        source_name="customers",
        source_file_path=Path("customers.csv"),
    )

    with pytest.raises(AttributeError):
        request.source_name = "orders"  # type: ignore[misc]


def test_ingestion_outcome_values_are_stable() -> None:
    assert IngestionOutcome.SUCCESS.value == "SUCCESS"
    assert IngestionOutcome.FAILED.value == "FAILED"


def test_successful_ingestion_result_captures_counts() -> None:
    result = IngestionResult(
        ingestion_run_id=10,
        ingestion_source_id=20,
        source_name="customers",
        source_file_path=Path("customers.csv"),
        outcome=IngestionOutcome.SUCCESS,
        rows_read=5000,
        rows_loaded=4997,
    )

    assert result.outcome is IngestionOutcome.SUCCESS
    assert result.rows_read == 5000
    assert result.rows_loaded == 4997
    assert result.error_message is None


def test_failed_ingestion_result_captures_error() -> None:
    result = IngestionResult(
        ingestion_run_id=10,
        ingestion_source_id=20,
        source_name="customers",
        source_file_path=Path("customers.csv"),
        outcome=IngestionOutcome.FAILED,
        rows_read=5000,
        rows_loaded=0,
        error_message="Raw database load failed.",
    )

    assert result.outcome is IngestionOutcome.FAILED
    assert result.rows_read == 5000
    assert result.rows_loaded == 0
    assert result.error_message == "Raw database load failed."


def test_ingestion_result_is_immutable() -> None:
    result = IngestionResult(
        ingestion_run_id=10,
        ingestion_source_id=20,
        source_name="customers",
        source_file_path=Path("customers.csv"),
        outcome=IngestionOutcome.SUCCESS,
        rows_read=5000,
        rows_loaded=5000,
    )

    with pytest.raises(AttributeError):
        result.rows_loaded = 0  # type: ignore[misc]
