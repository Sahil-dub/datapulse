from pathlib import Path

import pandas as pd
import pytest

from datapulse.data_generation.materialization import write_source_csv


def test_write_source_csv_creates_parent_directory(tmp_path: Path) -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["c001", "c002"],
            "country": ["DE", "FR"],
        }
    )
    output_path = tmp_path / "nested" / "customers.csv"

    result = write_source_csv(dataframe, output_path)

    assert result == output_path
    assert output_path.exists()

    written = pd.read_csv(output_path)
    pd.testing.assert_frame_equal(written, dataframe)


def test_write_source_csv_preserves_column_order(tmp_path: Path) -> None:
    dataframe = pd.DataFrame(
        {
            "product_id": ["p001"],
            "unit_price": [19.99],
            "category": ["ELECTRONICS"],
        }
    )
    output_path = tmp_path / "products.csv"

    write_source_csv(dataframe, output_path)

    written = pd.read_csv(output_path)

    assert list(written.columns) == [
        "product_id",
        "unit_price",
        "category",
    ]


def test_write_source_csv_overwrites_existing_file(tmp_path: Path) -> None:
    output_path = tmp_path / "customers.csv"

    first_dataframe = pd.DataFrame(
        {
            "customer_id": ["c001"],
            "country": ["DE"],
        }
    )
    second_dataframe = pd.DataFrame(
        {
            "customer_id": ["c002"],
            "country": ["FR"],
        }
    )

    write_source_csv(first_dataframe, output_path)
    write_source_csv(second_dataframe, output_path)

    written = pd.read_csv(output_path)

    pd.testing.assert_frame_equal(written, second_dataframe)


def test_write_source_csv_rejects_empty_dataframe(tmp_path: Path) -> None:
    dataframe = pd.DataFrame(columns=["customer_id", "country"])
    output_path = tmp_path / "customers.csv"

    with pytest.raises(ValueError, match="empty source dataset"):
        write_source_csv(dataframe, output_path)

    assert not output_path.exists()
