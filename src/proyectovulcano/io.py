from __future__ import annotations

import json
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


def list_numeric_columns(df: pd.DataFrame) -> list[str]:
    """Return numeric columns suitable for variables like grade/density."""
    out: list[str] = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            out.append(col)
    return out


def list_categorical_columns(df: pd.DataFrame) -> list[str]:
    """Return non-numeric columns that can be used for domain filters."""
    out: list[str] = []
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            out.append(col)
    return out


def export_dataframe_csv(df: pd.DataFrame, file_path: str | Path,
                         precision: int = 4) -> None:
    """Export dataframe to CSV with configurable precision."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format=f"%.{precision}f")


def export_dataframe_json(df: pd.DataFrame, file_path: str | Path) -> None:
    """Export dataframe to JSON."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(path, orient="records", indent=2)


def export_dataframe_xlsx(df: pd.DataFrame, file_path: str | Path) -> None:
    """Export dataframe to Excel (requires openpyxl)."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False)


def export_metadata(metadata: dict, file_path: str | Path) -> None:
    """Export metadata/config to JSON."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)


def import_drillholes_from_json(file_path: str | Path) -> pd.DataFrame:
    """Import drillholes from JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            "JSON missing required columns: " + ", ".join(missing)
        )
    
    return df

