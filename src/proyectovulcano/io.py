from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = ["hole_id", "x", "y", "z"]


def load_drillholes_csv(file_path: str | Path) -> pd.DataFrame:
    """Load and validate drillhole point data from CSV."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(path)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            "CSV missing required columns: " + ", ".join(missing)
        )

    for axis in ["x", "y", "z"]:
        df[axis] = pd.to_numeric(df[axis], errors="coerce")

    if df[["x", "y", "z"]].isna().any().any():
        raise ValueError("Columns x, y, z must be numeric and non-null.")

    return df


def filter_by_domain(
    df: pd.DataFrame,
    domain_col: str | None = None,
    domain_values: list[str] | None = None,
) -> pd.DataFrame:
    """Filter dataframe by categorical domain values."""
    if not domain_col:
        return df
    if domain_col not in df.columns:
        raise ValueError(f"Domain column not found: {domain_col}")

    if not domain_values:
        return df

    allowed = {str(v).strip() for v in domain_values if str(v).strip()}
    if not allowed:
        return df

    mask = df[domain_col].astype(str).isin(allowed)
    return df.loc[mask].copy()
