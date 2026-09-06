from pathlib import Path

import pandas as pd
import pytest

from datapulse.data_generation.manifest import (
    build_source_manifest,
    build_source_manifest_entry,
    calculate_file_sha256,
)


def test_calculate_file_sha256_returns_expected_hash(tmp_path: Path) -> None:
    file_path = tmp_path / "source.csv"
    file_path.write_text("id,value\n1,100\n", encoding="utf-8")

    first_hash = calculate_file_sha256(file_path)
    second_hash = calculate_file_sha256(file_path)

    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_calculate_file_sha256_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        calculate_file_sha256(tmp_path / "missing.csv")


def test_build_source_manifest_entry_contains_file_metadata(
    tmp_path: Path,
) -> None:
    dataframe = pd.DataFrame(
        {
            "id": [1, 2],
            "value": ["A", "B"],
        }
    )
    file_path = tmp_path / "customers.csv"
    dataframe.to_csv(file_path, index=False)

    entry = build_source_manifest_entry(
        source_name="customers",
        dataframe=dataframe,
        file_path=file_path,
    )

    assert entry["source_name"] == "customers"
    assert entry["file_path"] == str(file_path)
    assert entry["row_count"] == 2
    assert entry["columns"] == ["id", "value"]
    assert entry["file_size_bytes"] == file_path.stat().st_size
    assert isinstance(entry["file_sha256"], str)
    assert len(entry["file_sha256"]) == 64


def test_build_source_manifest_rejects_empty_entries() -> None:
    with pytest.raises(ValueError, match="without source entries"):
        build_source_manifest([])


def test_build_source_manifest_rejects_duplicate_source_names() -> None:
    entries = [
        {
            "source_name": "customers",
            "row_count": 10,
        },
        {
            "source_name": "customers",
            "row_count": 20,
        },
    ]

    with pytest.raises(ValueError, match="unique"):
        build_source_manifest(entries)


def test_build_source_manifest_contains_generation_timestamp() -> None:
    entries = [
        {
            "source_name": "customers",
            "row_count": 10,
        }
    ]

    manifest = build_source_manifest(entries)

    assert "generated_at" in manifest
    assert manifest["sources"] == entries
