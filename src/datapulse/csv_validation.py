from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


class CSVValidationError(ValueError):
    """Raised when a source CSV violates its expected structural contract."""


def validate_csv_schema(
    dataframe: pd.DataFrame,
    expected_columns: Sequence[str],
    source_name: str,
) -> None:
    """Validate the structural schema of a source CSV DataFrame."""
    if not source_name:
        raise CSVValidationError("source_name must not be empty.")

    if dataframe.empty:
        raise CSVValidationError(f"{source_name}: source CSV must contain at least one row.")

    actual_columns = list(dataframe.columns)
    expected = list(expected_columns)

    if len(actual_columns) != len(set(actual_columns)):
        raise CSVValidationError(f"{source_name}: source CSV contains duplicate column names.")

    missing_columns = [column for column in expected if column not in actual_columns]
    unexpected_columns = [column for column in actual_columns if column not in expected]

    errors: list[str] = []

    if missing_columns:
        errors.append(f"missing columns: {', '.join(missing_columns)}")

    if unexpected_columns:
        errors.append(f"unexpected columns: {', '.join(unexpected_columns)}")

    if errors:
        raise CSVValidationError(
            f"{source_name}: CSV schema validation failed: " + "; ".join(errors)
        )

    if actual_columns != expected:
        raise CSVValidationError(
            f"{source_name}: CSV column order mismatch "
            f"(expected={expected}, actual={actual_columns})."
        )
