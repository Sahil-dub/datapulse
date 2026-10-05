from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

from datapulse.ingestion_contract import IngestionOutcome, IngestionRequest
from datapulse.ingestion_orchestrator import ingest_source


def test_ingest_source_runs_successful_workflow(monkeypatch) -> None:
    engine = MagicMock()
    request = IngestionRequest(
        source_name="customers",
        source_file_path=Path("customers.csv"),
    )
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": "C001",
                "first_name": "Asha",
            },
            {
                "customer_id": "C002",
                "first_name": "Ravi",
            },
        ]
    )

    start_run = MagicMock(return_value=10)
    start_source = MagicMock(return_value=20)
    read_file = MagicMock(return_value=dataframe)
    validate_schema = MagicMock()
    load_raw = MagicMock(return_value=2)
    complete_source = MagicMock()
    complete_run = MagicMock()

    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_run",
        start_run,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_source",
        start_source,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.read_csv_file",
        read_file,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.validate_csv_schema",
        validate_schema,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.load_dataframe_to_raw_in_batches",
        load_raw,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_source",
        complete_source,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_run",
        complete_run,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.get_source_columns",
        MagicMock(return_value=("customer_id", "first_name")),
    )

    result = ingest_source(engine, request, batch_size=100)

    assert result.ingestion_run_id == 10
    assert result.ingestion_source_id == 20
    assert result.source_name == "customers"
    assert result.source_file_path == Path("customers.csv")
    assert result.outcome is IngestionOutcome.SUCCESS
    assert result.rows_read == 2
    assert result.rows_loaded == 2
    assert result.error_message is None

    start_run.assert_called_once_with(engine, source_name="customers")
    start_source.assert_called_once_with(
        engine,
        ingestion_run_id=10,
        request=request,
    )
    read_file.assert_called_once_with(Path("customers.csv"))
    validate_schema.assert_called_once_with(
        dataframe,
        expected_columns=("customer_id", "first_name"),
        source_name="customers",
    )
    load_raw.assert_called_once_with(
        engine,
        dataframe,
        source_name="customers",
        batch_size=100,
    )
    complete_source.assert_called_once_with(
        engine,
        ingestion_source_id=20,
        rows_read=2,
        rows_loaded=2,
    )
    complete_run.assert_called_once_with(
        engine,
        ingestion_run_id=10,
        rows_read=2,
        rows_loaded=2,
    )


def test_ingest_source_reads_rows_before_validation(monkeypatch) -> None:
    engine = MagicMock()
    request = IngestionRequest(
        source_name="customers",
        source_file_path=Path("customers.csv"),
    )
    dataframe = pd.DataFrame([{"customer_id": "C001"}])
    call_order: list[str] = []

    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_run",
        lambda *_args, **_kwargs: call_order.append("start_run") or 10,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_source",
        lambda *_args, **_kwargs: call_order.append("start_source") or 20,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.read_csv_file",
        lambda *_args, **_kwargs: call_order.append("read") or dataframe,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.get_source_columns",
        lambda *_args, **_kwargs: ("customer_id",),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.validate_csv_schema",
        lambda *_args, **_kwargs: call_order.append("validate"),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.load_dataframe_to_raw_in_batches",
        lambda *_args, **_kwargs: call_order.append("load") or 1,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_source",
        lambda *_args, **_kwargs: call_order.append("complete_source"),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_run",
        lambda *_args, **_kwargs: call_order.append("complete_run"),
    )

    result = ingest_source(engine, request)

    assert result.rows_read == 1
    assert call_order == [
        "start_run",
        "start_source",
        "read",
        "validate",
        "load",
        "complete_source",
        "complete_run",
    ]


def test_ingest_source_does_not_complete_metadata_before_load(monkeypatch) -> None:
    engine = MagicMock()
    request = IngestionRequest(
        source_name="customers",
        source_file_path=Path("customers.csv"),
    )
    dataframe = pd.DataFrame([{"customer_id": "C001"}])

    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_run",
        lambda *_args, **_kwargs: 10,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_source",
        lambda *_args, **_kwargs: 20,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.read_csv_file",
        lambda *_args, **_kwargs: dataframe,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.get_source_columns",
        lambda *_args, **_kwargs: ("customer_id",),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.validate_csv_schema",
        MagicMock(),
    )
    load_raw = MagicMock(return_value=1)
    complete_source = MagicMock()
    complete_run = MagicMock()
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.load_dataframe_to_raw_in_batches",
        load_raw,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_source",
        complete_source,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_run",
        complete_run,
    )

    ingest_source(engine, request)

    assert load_raw.call_count == 1
    assert complete_source.call_count == 1
    assert complete_run.call_count == 1
    assert load_raw.call_args_list[0] is not None


def test_ingest_source_uses_default_batch_size(monkeypatch) -> None:
    engine = MagicMock()
    request = IngestionRequest(
        source_name="customers",
        source_file_path=Path("customers.csv"),
    )
    dataframe = pd.DataFrame([{"customer_id": "C001"}])
    load_raw = MagicMock(return_value=1)

    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_run",
        lambda *_args, **_kwargs: 10,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_source",
        lambda *_args, **_kwargs: 20,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.read_csv_file",
        lambda *_args, **_kwargs: dataframe,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.get_source_columns",
        lambda *_args, **_kwargs: ("customer_id",),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.validate_csv_schema",
        MagicMock(),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.load_dataframe_to_raw_in_batches",
        load_raw,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_source",
        MagicMock(),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_run",
        MagicMock(),
    )

    ingest_source(engine, request)

    assert load_raw.call_args.kwargs["batch_size"] == 1_000


def test_ingest_source_short_circuits_after_schema_validation_failure(monkeypatch) -> None:
    engine = MagicMock()
    request = IngestionRequest(
        source_name="customers",
        source_file_path=Path("customers.csv"),
    )
    dataframe = pd.DataFrame([{"customer_id": "C001"}])
    validate_schema = MagicMock(side_effect=RuntimeError("schema validation failed"))
    load_raw = MagicMock()
    fail_source = MagicMock()
    fail_run = MagicMock()

    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_run",
        MagicMock(return_value=10),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_source",
        MagicMock(return_value=20),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.read_csv_file",
        MagicMock(return_value=dataframe),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.get_source_columns",
        MagicMock(return_value=("customer_id",)),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.validate_csv_schema",
        validate_schema,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.load_dataframe_to_raw_in_batches",
        load_raw,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.fail_ingestion_source",
        fail_source,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.fail_ingestion_run",
        fail_run,
    )

    result = ingest_source(engine, request)

    assert result.outcome is IngestionOutcome.FAILED
    validate_schema.assert_called_once()
    load_raw.assert_not_called()
    fail_source.assert_called_once()
    fail_run.assert_called_once()


def test_ingest_source_completes_source_before_run(monkeypatch) -> None:
    engine = MagicMock()
    request = IngestionRequest(
        source_name="customers",
        source_file_path=Path("customers.csv"),
    )
    dataframe = pd.DataFrame([{"customer_id": "C001"}])
    call_order: list[str] = []

    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_run",
        lambda *_args, **_kwargs: call_order.append("start_run") or 10,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_source",
        lambda *_args, **_kwargs: call_order.append("start_source") or 20,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.read_csv_file",
        lambda *_args, **_kwargs: call_order.append("read") or dataframe,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.get_source_columns",
        lambda *_args, **_kwargs: ("customer_id",),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.validate_csv_schema",
        lambda *_args, **_kwargs: call_order.append("validate"),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.load_dataframe_to_raw_in_batches",
        lambda *_args, **_kwargs: call_order.append("load") or 1,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_source",
        lambda *_args, **_kwargs: call_order.append("complete_source"),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_run",
        lambda *_args, **_kwargs: call_order.append("complete_run"),
    )

    result = ingest_source(engine, request)

    assert result.outcome is IngestionOutcome.SUCCESS
    assert call_order == [
        "start_run",
        "start_source",
        "read",
        "validate",
        "load",
        "complete_source",
        "complete_run",
    ]


def test_ingest_source_propagates_metadata_start_failure(monkeypatch) -> None:
    engine = MagicMock()
    request = IngestionRequest(
        source_name="customers",
        source_file_path=Path("customers.csv"),
    )
    start_error = RuntimeError("metadata database unavailable")
    start_run = MagicMock(side_effect=start_error)
    start_source = MagicMock()

    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_run",
        start_run,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_source",
        start_source,
    )

    try:
        ingest_source(engine, request)
    except RuntimeError as exc:
        assert exc is start_error
    else:
        raise AssertionError("metadata start failure was not propagated")

    start_run.assert_called_once_with(engine, source_name="customers")
    start_source.assert_not_called()


def test_ingest_source_marks_failure_when_file_read_fails(monkeypatch) -> None:
    engine = MagicMock()
    request = IngestionRequest(
        source_name="customers",
        source_file_path=Path("customers.csv"),
    )
    start_run = MagicMock(return_value=10)
    start_source = MagicMock(return_value=20)
    read_file = MagicMock(side_effect=RuntimeError("source file is unavailable"))
    fail_source = MagicMock()
    fail_run = MagicMock()
    complete_source = MagicMock()
    complete_run = MagicMock()

    monkeypatch.setattr("datapulse.ingestion_orchestrator.start_ingestion_run", start_run)
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_source",
        start_source,
    )
    monkeypatch.setattr("datapulse.ingestion_orchestrator.read_csv_file", read_file)
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.fail_ingestion_source",
        fail_source,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.fail_ingestion_run",
        fail_run,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_source",
        complete_source,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_run",
        complete_run,
    )

    result = ingest_source(engine, request)

    assert result.outcome is IngestionOutcome.FAILED
    assert result.rows_read == 0
    assert result.rows_loaded == 0
    assert result.error_message == "source file is unavailable"

    fail_source.assert_called_once_with(
        engine,
        ingestion_source_id=20,
        rows_read=0,
        rows_loaded=0,
        error_message="source file is unavailable",
    )
    fail_run.assert_called_once_with(
        engine,
        ingestion_run_id=10,
        rows_read=0,
        rows_loaded=0,
        error_message="source file is unavailable",
    )
    complete_source.assert_not_called()
    complete_run.assert_not_called()


def test_ingest_source_marks_failure_when_schema_validation_fails(monkeypatch) -> None:
    engine = MagicMock()
    request = IngestionRequest(
        source_name="customers",
        source_file_path=Path("customers.csv"),
    )
    dataframe = pd.DataFrame([{"customer_id": "C001"}])
    validation_error = RuntimeError("schema validation failed")
    fail_source = MagicMock()
    fail_run = MagicMock()

    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_run",
        MagicMock(return_value=10),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_source",
        MagicMock(return_value=20),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.read_csv_file",
        MagicMock(return_value=dataframe),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.get_source_columns",
        MagicMock(return_value=("customer_id",)),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.validate_csv_schema",
        MagicMock(side_effect=validation_error),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.fail_ingestion_source",
        fail_source,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.fail_ingestion_run",
        fail_run,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_source",
        MagicMock(),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_run",
        MagicMock(),
    )

    result = ingest_source(engine, request)

    assert result.outcome is IngestionOutcome.FAILED
    assert result.rows_read == 1
    assert result.rows_loaded == 0
    assert result.error_message == "schema validation failed"

    fail_source.assert_called_once_with(
        engine,
        ingestion_source_id=20,
        rows_read=1,
        rows_loaded=0,
        error_message="schema validation failed",
    )
    fail_run.assert_called_once_with(
        engine,
        ingestion_run_id=10,
        rows_read=1,
        rows_loaded=0,
        error_message="schema validation failed",
    )


def test_ingest_source_marks_database_load_failure_with_zero_rows_loaded(
    monkeypatch,
) -> None:
    engine = MagicMock()
    request = IngestionRequest(
        source_name="customers",
        source_file_path=Path("customers.csv"),
    )
    dataframe = pd.DataFrame(
        [
            {"customer_id": "C001"},
            {"customer_id": "C002"},
        ]
    )
    load_error = RuntimeError("raw load failed")
    fail_source = MagicMock()
    fail_run = MagicMock()

    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_run",
        MagicMock(return_value=10),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.start_ingestion_source",
        MagicMock(return_value=20),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.read_csv_file",
        MagicMock(return_value=dataframe),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.get_source_columns",
        MagicMock(return_value=("customer_id",)),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.validate_csv_schema",
        MagicMock(),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.load_dataframe_to_raw_in_batches",
        MagicMock(side_effect=load_error),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.fail_ingestion_source",
        fail_source,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.fail_ingestion_run",
        fail_run,
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_source",
        MagicMock(),
    )
    monkeypatch.setattr(
        "datapulse.ingestion_orchestrator.complete_ingestion_run",
        MagicMock(),
    )

    result = ingest_source(engine, request)

    assert result.outcome is IngestionOutcome.FAILED
    assert result.rows_read == 2
    assert result.rows_loaded == 0
    assert result.error_message == "raw load failed"

    fail_source.assert_called_once_with(
        engine,
        ingestion_source_id=20,
        rows_read=2,
        rows_loaded=0,
        error_message="raw load failed",
    )
    fail_run.assert_called_once_with(
        engine,
        ingestion_run_id=10,
        rows_read=2,
        rows_loaded=0,
        error_message="raw load failed",
    )
