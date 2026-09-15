import pandas as pd
import pytest

from datapulse.csv_validation import (
    CSVValidationError,
    validate_csv_schema,
)

EXPECTED_COLUMNS = (
    "customer_id",
    "email",
)


def test_validate_csv_schema_passes_for_expected_schema() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["CUST-000001"],
            "email": ["test@example.com"],
        }
    )

    validate_csv_schema(
        dataframe,
        expected_columns=EXPECTED_COLUMNS,
        source_name="customers",
    )


def test_validate_csv_schema_rejects_empty_dataset() -> None:
    dataframe = pd.DataFrame(columns=EXPECTED_COLUMNS)

    with pytest.raises(
        CSVValidationError,
        match="source CSV must contain at least one row",
    ):
        validate_csv_schema(
            dataframe,
            expected_columns=EXPECTED_COLUMNS,
            source_name="customers",
        )


def test_validate_csv_schema_rejects_missing_column() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["CUST-000001"],
        }
    )

    with pytest.raises(
        CSVValidationError,
        match="missing columns: email",
    ):
        validate_csv_schema(
            dataframe,
            expected_columns=EXPECTED_COLUMNS,
            source_name="customers",
        )


def test_validate_csv_schema_rejects_unexpected_column() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["CUST-000001"],
            "email": ["test@example.com"],
            "email_address": ["test@example.com"],
        }
    )

    with pytest.raises(
        CSVValidationError,
        match="unexpected columns: email_address",
    ):
        validate_csv_schema(
            dataframe,
            expected_columns=EXPECTED_COLUMNS,
            source_name="customers",
        )


def test_validate_csv_schema_rejects_column_order_mismatch() -> None:
    dataframe = pd.DataFrame(
        {
            "email": ["test@example.com"],
            "customer_id": ["CUST-000001"],
        }
    )

    with pytest.raises(
        CSVValidationError,
        match="column order mismatch",
    ):
        validate_csv_schema(
            dataframe,
            expected_columns=EXPECTED_COLUMNS,
            source_name="customers",
        )


def test_validate_csv_schema_rejects_duplicate_columns() -> None:
    dataframe = pd.DataFrame(
        [
            ["CUST-000001", "test@example.com"],
        ],
        columns=["customer_id", "customer_id"],
    )

    with pytest.raises(
        CSVValidationError,
        match="duplicate column names",
    ):
        validate_csv_schema(
            dataframe,
            expected_columns=("customer_id",),
            source_name="customers",
        )


def test_validate_csv_schema_rejects_empty_source_name() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["CUST-000001"],
            "email": ["test@example.com"],
        }
    )

    with pytest.raises(
        CSVValidationError,
        match="source_name must not be empty",
    ):
        validate_csv_schema(
            dataframe,
            expected_columns=EXPECTED_COLUMNS,
            source_name="",
        )
