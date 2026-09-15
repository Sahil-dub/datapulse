from unittest.mock import MagicMock

import pandas as pd
import pytest

from datapulse.db_loader import DBLoaderError, load_dataframe_to_raw


def test_load_dataframe_to_raw_inserts_source_rows() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["CUST-000001", "CUST-000002"],
            "first_name": ["Alice", "Bob"],
            "last_name": ["Smith", "Jones"],
            "email": ["alice@example.com", "bob@example.com"],
            "country": ["DE", "FR"],
            "signup_date": ["2025-01-01", "2025-01-02"],
            "customer_status": ["active", "active"],
            "acquisition_channel": ["organic", "paid"],
        }
    )

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
