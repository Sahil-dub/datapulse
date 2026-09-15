from __future__ import annotations

from collections.abc import Mapping

import pandas as pd
from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import SQLAlchemyError

from datapulse.source_schema import get_source_columns

RAW_TABLES: Mapping[str, str] = {
    "customers": "raw.customers",
    "products": "raw.products",
    "orders": "raw.orders",
    "payments": "raw.payments",
    "subscriptions": "raw.subscriptions",
    "support_tickets": "raw.support_tickets",
    "web_events": "raw.web_events",
}


class DBLoaderError(RuntimeError):
    """Raised when source data cannot be loaded into a raw database table."""


def _validate_dataframe(
    dataframe: pd.DataFrame,
    source_name: str,
) -> tuple[str, ...]:
    """Validate the source and DataFrame before loading."""
    if source_name not in RAW_TABLES:
        raise DBLoaderError(f"Unknown source: {source_name}")

    if dataframe.empty:
        raise DBLoaderError(f"{source_name}: cannot load an empty DataFrame.")

    source_columns = get_source_columns(source_name)

    actual_columns = list(dataframe.columns)
    missing_columns = [column for column in source_columns if column not in actual_columns]

    if missing_columns:
        raise DBLoaderError(
            f"{source_name}: DataFrame is missing required columns: {', '.join(missing_columns)}"
        )

    return source_columns


def _build_insert_statement(
    source_name: str,
    source_columns: tuple[str, ...],
):
    """Build the parameterized INSERT statement for a raw source table."""
    column_list = ", ".join(source_columns)
    parameter_list = ", ".join(f":{column}" for column in source_columns)

    return text(f"INSERT INTO {RAW_TABLES[source_name]} ({column_list}) VALUES ({parameter_list})")


def _load_rows(
    connection: Connection,
    source_name: str,
    source_columns: tuple[str, ...],
    rows: list[dict[str, object]],
) -> None:
    """Insert one batch of source rows using an existing transaction."""
    insert_statement = _build_insert_statement(source_name, source_columns)
    connection.execute(insert_statement, rows)


def load_dataframe_to_raw(
    engine: Engine,
    dataframe: pd.DataFrame,
    source_name: str,
) -> int:
    """Load a source DataFrame into its corresponding raw database table."""
    source_columns = _validate_dataframe(dataframe, source_name)

    rows = dataframe.loc[:, source_columns].to_dict(orient="records")

    try:
        with engine.begin() as connection:
            _load_rows(connection, source_name, source_columns, rows)
    except SQLAlchemyError as exc:
        raise DBLoaderError(
            f"{source_name}: failed to load data into {RAW_TABLES[source_name]}."
        ) from exc

    return len(rows)


def load_dataframe_to_raw_in_batches(
    engine: Engine,
    dataframe: pd.DataFrame,
    source_name: str,
    batch_size: int,
) -> int:
    """Load a source DataFrame into a raw table using one transaction."""
    source_columns = _validate_dataframe(dataframe, source_name)

    if batch_size <= 0:
        raise DBLoaderError("batch_size must be greater than zero.")

    total_rows = len(dataframe)

    try:
        with engine.begin() as connection:
            for start in range(0, total_rows, batch_size):
                batch = dataframe.iloc[start : start + batch_size]
                rows = batch.loc[:, source_columns].to_dict(orient="records")
                _load_rows(connection, source_name, source_columns, rows)
    except SQLAlchemyError as exc:
        raise DBLoaderError(
            f"{source_name}: failed to load data into {RAW_TABLES[source_name]}."
        ) from exc

    return total_rows
