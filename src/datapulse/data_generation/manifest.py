from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


def calculate_file_sha256(file_path: str | Path) -> str:
    """Calculate the SHA-256 hash of a file."""
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Source file does not exist: {path}")

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def build_source_manifest_entry(
    source_name: str,
    dataframe: pd.DataFrame,
    file_path: str | Path,
) -> dict[str, object]:
    """Build manifest metadata for one materialized source file."""
    path = Path(file_path)

    if not source_name:
        raise ValueError("source_name must not be empty.")

    if dataframe.empty:
        raise ValueError("Cannot build a manifest entry for an empty dataset.")

    if not path.is_file():
        raise FileNotFoundError(f"Source file does not exist: {path}")

    return {
        "source_name": source_name,
        "file_path": str(path),
        "row_count": len(dataframe),
        "columns": list(dataframe.columns),
        "file_size_bytes": path.stat().st_size,
        "file_sha256": calculate_file_sha256(path),
    }


def build_source_manifest(
    entries: list[dict[str, object]],
    schema_drift_scenarios: tuple[str, ...] = (),
) -> dict[str, object]:
    """Build the top-level manifest for materialized source files."""
    if not entries:
        raise ValueError("Cannot build a manifest without source entries.")

    source_names = [entry["source_name"] for entry in entries]

    if len(source_names) != len(set(source_names)):
        raise ValueError("Manifest source names must be unique.")

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "schema_drift_scenarios": list(schema_drift_scenarios),
        "sources": entries,
    }


def write_source_manifest(
    manifest: dict[str, object],
    output_path: str | Path,
) -> Path:
    """Write a source manifest to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    return path
