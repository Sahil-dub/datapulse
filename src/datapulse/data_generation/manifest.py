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


def validate_source_manifest(manifest_path: str | Path) -> None:
    """Validate manifest metadata against materialized source files."""
    path = Path(manifest_path)

    if not path.is_file():
        raise FileNotFoundError(f"Manifest file does not exist: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            manifest = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Manifest is not valid JSON: {path}") from exc

    sources = manifest.get("sources")

    if not isinstance(sources, list) or not sources:
        raise ValueError("Manifest must contain a non-empty 'sources' list.")

    required_fields = {
        "source_name",
        "file_path",
        "row_count",
        "columns",
        "file_size_bytes",
        "file_sha256",
    }
    source_names: list[str] = []
    errors: list[str] = []

    for index, entry in enumerate(sources):
        if not isinstance(entry, dict):
            errors.append(f"sources[{index}] must be an object.")
            continue

        missing_fields = required_fields - entry.keys()

        if missing_fields:
            errors.append(
                f"sources[{index}] is missing fields: {', '.join(sorted(missing_fields))}."
            )
            continue

        source_name = entry["source_name"]

        if not isinstance(source_name, str) or not source_name:
            errors.append(f"sources[{index}] has an invalid source_name.")
            continue

        source_names.append(source_name)
        source_path = Path(str(entry["file_path"]))

        if not source_path.is_absolute():
            source_path = path.parent / source_path

        if not source_path.is_file():
            errors.append(f"{source_name}: source file does not exist: {source_path}")
            continue

        try:
            dataframe = pd.read_csv(source_path)
        except (pd.errors.ParserError, UnicodeDecodeError) as exc:
            errors.append(f"{source_name}: unable to read source CSV: {exc}")
            continue

        actual_columns = list(dataframe.columns)
        actual_row_count = len(dataframe)
        actual_size = source_path.stat().st_size
        actual_hash = calculate_file_sha256(source_path)

        if entry["row_count"] != actual_row_count:
            errors.append(
                f"{source_name}: row count mismatch "
                f"(manifest={entry['row_count']}, actual={actual_row_count})."
            )

        if entry["columns"] != actual_columns:
            errors.append(
                f"{source_name}: column mismatch "
                f"(manifest={entry['columns']}, actual={actual_columns})."
            )

        if entry["file_size_bytes"] != actual_size:
            errors.append(
                f"{source_name}: file size mismatch "
                f"(manifest={entry['file_size_bytes']}, actual={actual_size})."
            )

        if entry["file_sha256"] != actual_hash:
            errors.append(f"{source_name}: SHA-256 mismatch.")

    if len(source_names) != len(set(source_names)):
        errors.append("Manifest source names must be unique.")

    if errors:
        raise ValueError("Manifest validation failed:\n- " + "\n- ".join(errors))
