from unittest.mock import MagicMock

import pandas as pd
import pytest
from sqlalchemy.exc import SQLAlchemyError

from datapulse.db_loader import (
    DBLoaderError,
    load_dataframe_to_raw,
    load_dataframe_to_raw_in_batches,
)


def _customer_dataframe(row_count: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": [f"CUST-{index:06d}" for index in range(row_count)],
            "first_name": [f"First{index}" for index in range(row_count)],
            "last_name": [f"Last{index}" for index in range(row_count)],
            "email": [f"user{index}@example.com" for index in range(row_count)],
            "country": ["DE"] * row_count,
            "signup_date": ["2025-01-01"] * row_count,
            "customer_status": ["active"] * row_count,
            "acquisition_channel": ["organic"] * row_count,
        }
    )


def test_load_dataframe_to_raw_inserts_source_rows() -> None:
    dataframe = _customer_dataframe(2)
    engine = MagicMock()

    assert load_dataframe_to_raw(engine, dataframe, "customers") == 2

    connection = engine.begin.return_value.__enter__.return_value
    connection.execute.assert_called_once()

    statement, rows = connection.execute.call_args.args

    assert "INSERT INTO raw.customers" in str(statement)
    assert "raw_record_id" not in str(statement)
    assert len(rows) == 2


def test_load_dataframe_to_raw_rejects_unknown_source() -> None:
    engine = MagicMock()
    dataframe = pd.DataFrame({"value": ["test"]})

    with pytest.raises(
        DBLoaderError,
        match="Unknown source: unknown",
    ):
        load_dataframe_to_raw(engine, dataframe, "unknown")


def test_load_dataframe_to_raw_rejects_empty_dataframe() -> None:
    engine = MagicMock()
    dataframe = pd.DataFrame(
        columns=[
            "customer_id",
            "first_name",
            "last_name",
            "email",
            "country",
            "signup_date",
            "customer_status",
            "acquisition_channel",
        ]
    )

    with pytest.raises(
        DBLoaderError,
        match="customers: cannot load an empty DataFrame",
    ):
        load_dataframe_to_raw(engine, dataframe, "customers")


def test_load_dataframe_to_raw_rejects_missing_columns() -> None:
    engine = MagicMock()
    dataframe = pd.DataFrame(
        {
            "customer_id": ["CUST-000001"],
        }
    )

    with pytest.raises(
        DBLoaderError,
        match="customers: DataFrame is missing required columns",
    ):
        load_dataframe_to_raw(engine, dataframe, "customers")


def test_load_dataframe_to_raw_in_batches_splits_rows_into_batches() -> None:
    dataframe = _customer_dataframe(5)
    engine = MagicMock()

    assert (
        load_dataframe_to_raw_in_batches(
            engine,
            dataframe,
            "customers",
            batch_size=2,
        )
        == 5
    )

    connection = engine.begin.return_value.__enter__.return_value

    assert connection.execute.call_count == 3

    batches = [call.args[1] for call in connection.execute.call_args_list]

    assert [len(batch) for batch in batches] == [2, 2, 1]


def test_load_dataframe_to_raw_in_batches_handles_exact_batch_size() -> None:
    dataframe = _customer_dataframe(4)
    engine = MagicMock()

    assert (
        load_dataframe_to_raw_in_batches(
            engine,
            dataframe,
            "customers",
            batch_size=2,
        )
        == 4
    )

    connection = engine.begin.return_value.__enter__.return_value
    assert connection.execute.call_count == 2


def test_load_dataframe_to_raw_in_batches_rejects_invalid_batch_size() -> None:
    dataframe = _customer_dataframe(2)
    engine = MagicMock()

    with pytest.raises(
        DBLoaderError,
        match="batch_size must be greater than zero",
    ):
        load_dataframe_to_raw_in_batches(
            engine,
            dataframe,
            "customers",
            batch_size=0,
        )


def test_load_dataframe_to_raw_in_batches_rejects_negative_batch_size() -> None:
    dataframe = _customer_dataframe(2)
    engine = MagicMock()

    with pytest.raises(
        DBLoaderError,
        match="batch_size must be greater than zero",
    ):
        load_dataframe_to_raw_in_batches(
            engine,
            dataframe,
            "customers",
            batch_size=-10,
        )


def test_load_dataframe_to_raw_in_batches_uses_one_transaction() -> None:
    dataframe = _customer_dataframe(5)
    engine = MagicMock()

    assert (
        load_dataframe_to_raw_in_batches(
            engine,
            dataframe,
            "customers",
            batch_size=2,
        )
        == 5
    )

    assert engine.begin.call_count == 1

    connection = engine.begin.return_value.__enter__.return_value
    assert connection.execute.call_count == 3

    batches = [call.args[1] for call in connection.execute.call_args_list]
    assert [len(batch) for batch in batches] == [2, 2, 1]


def test_load_dataframe_to_raw_in_batches_stops_after_batch_failure() -> None:
    dataframe = _customer_dataframe(5)
    engine = MagicMock()

    connection = engine.begin.return_value.__enter__.return_value
    connection.execute.side_effect = [
        None,
        SQLAlchemyError("database failure"),
    ]

    with pytest.raises(
        DBLoaderError,
        match="customers: failed to load batch 2 into raw.customers",
    ):
        load_dataframe_to_raw_in_batches(
            engine,
            dataframe,
            "customers",
            batch_size=2,
        )

    assert engine.begin.call_count == 1
    assert connection.execute.call_count == 2


def test_load_dataframe_to_raw_preserves_database_error_as_cause() -> None:
    dataframe = _customer_dataframe(2)
    engine = MagicMock()

    database_error = SQLAlchemyError("database unavailable")
    connection = engine.begin.return_value.__enter__.return_value
    connection.execute.side_effect = database_error

    with pytest.raises(
        DBLoaderError,
        match="customers: failed to load data into raw.customers",
    ) as exc_info:
        load_dataframe_to_raw(engine, dataframe, "customers")

    assert exc_info.value.__cause__ is database_error


def test_load_dataframe_to_raw_in_batches_reports_failed_batch() -> None:
    dataframe = _customer_dataframe(5)
    engine = MagicMock()

    database_error = SQLAlchemyError("database failure")
    connection = engine.begin.return_value.__enter__.return_value
    connection.execute.side_effect = [
        None,
        database_error,
    ]

    with pytest.raises(
        DBLoaderError,
        match="customers: failed to load batch 2 into raw.customers",
    ) as exc_info:
        load_dataframe_to_raw_in_batches(
            engine,
            dataframe,
            "customers",
            batch_size=2,
        )

    assert exc_info.value.__cause__ is database_error
    assert connection.execute.call_count == 2


def test_load_dataframe_to_raw_in_batches_does_not_swallow_unexpected_errors() -> None:
    dataframe = _customer_dataframe(5)
    engine = MagicMock()

    connection = engine.begin.return_value.__enter__.return_value
    unexpected_error = TypeError("unexpected programming error")
    connection.execute.side_effect = unexpected_error

    with pytest.raises(TypeError, match="unexpected programming error"):
        load_dataframe_to_raw_in_batches(
            engine,
            dataframe,
            "customers",
            batch_size=2,
        )
