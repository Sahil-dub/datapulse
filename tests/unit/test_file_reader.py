from pathlib import Path

import pandas as pd
import pytest

from datapulse.file_reader import FileReaderError, read_csv_file


def test_read_csv_file_returns_dataframe(tmp_path: Path) -> None:
    source_file = tmp_path / "customers.csv"
    source_file.write_text(
        "customer_id,email\nCUST-000001,test@example.com\n",
        encoding="utf-8",
    )

    result = read_csv_file(source_file)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["customer_id", "email"]
    assert result.iloc[0]["customer_id"] == "CUST-000001"
    assert result.iloc[0]["email"] == "test@example.com"


def test_read_csv_file_preserves_missing_values(tmp_path: Path) -> None:
    source_file = tmp_path / "customers.csv"
    source_file.write_text(
        "customer_id,email\nCUST-000001,\n",
        encoding="utf-8",
    )

    result = read_csv_file(source_file)

    assert pd.isna(result.iloc[0]["email"])


def test_read_csv_file_rejects_unsupported_file_type(tmp_path: Path) -> None:
    source_file = tmp_path / "customers.txt"
    source_file.write_text("customer_id\nCUST-000001\n", encoding="utf-8")

    with pytest.raises(
        FileReaderError,
        match="Unsupported source file type",
    ):
        read_csv_file(source_file)


def test_read_csv_file_rejects_missing_file(tmp_path: Path) -> None:
    source_file = tmp_path / "missing.csv"

    with pytest.raises(
        FileReaderError,
        match="Source file does not exist",
    ):
        read_csv_file(source_file)


def test_read_csv_file_rejects_directory(tmp_path: Path) -> None:
    source_directory = tmp_path / "customers.csv"
    source_directory.mkdir()

    with pytest.raises(
        FileReaderError,
        match="Source path is not a file",
    ):
        read_csv_file(source_directory)
