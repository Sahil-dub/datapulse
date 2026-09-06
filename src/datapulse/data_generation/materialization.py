from pathlib import Path

import pandas as pd


def write_source_csv(
    dataframe: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Write a generated source dataset to a CSV file.

    The destination directory is created automatically. Empty datasets are
    rejected because a source extract without rows is likely an error at this
    stage of the synthetic data pipeline.
    """
    if dataframe.empty:
        raise ValueError("Cannot materialize an empty source dataset.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    dataframe.to_csv(path, index=False)

    return path
