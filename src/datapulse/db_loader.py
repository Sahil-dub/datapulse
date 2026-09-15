from __future__ import annotations

from collections.abc import Mapping

import pandas as pd
from sqlalchemy import Engine, text
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


def load_dataframe_to_raw(
    engine: Engine,
    dataframe: pd.DataFrame,
    source_name: str,
) -> int:
    """Load a source DataFrame into its corresponding raw database table."""
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

    rows = dataframe.loc[:, source_columns].to_dict(orient="records")
    column_list = ", ".join(source_columns)
    parameter_list = ", ".join(f":{column}" for column in source_columns)

    insert_statement = text(
        f"INSERT INTO {RAW_TABLES[source_name]} ({column_list}) VALUES ({parameter_list})"
    )

    try:
        with engine.begin() as connection:
            connection.execute(insert_statement, rows)
    except SQLAlchemyError as exc:
        raise DBLoaderError(
            f"{source_name}: failed to load data into {RAW_TABLES[source_name]}."
        ) from exc

    return len(rows)
