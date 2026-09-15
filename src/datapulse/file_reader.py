from pathlib import Path

import pandas as pd


class FileReaderError(RuntimeError):
    """Raised when a source file cannot be read by the ingestion file reader."""


def read_csv_file(path: Path) -> pd.DataFrame:
    """Read a CSV source file into a pandas DataFrame."""
    if path.suffix.lower() != ".csv":
        raise FileReaderError(f"Unsupported source file type: {path.suffix}")

    if not path.exists():
        raise FileReaderError(f"Source file does not exist: {path}")

    if not path.is_file():
        raise FileReaderError(f"Source path is not a file: {path}")

    try:
        return pd.read_csv(path, dtype="string")
    except (OSError, UnicodeDecodeError, pd.errors.ParserError) as exc:
        raise FileReaderError(f"Failed to read source file: {path}") from exc
