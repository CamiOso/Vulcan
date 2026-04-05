from __future__ import annotations

import numpy as np
import pandas as pd


def _series_stats(s: pd.Series) -> dict[str, float]:
    """Compute statistics for a numeric series."""
    x = pd.to_numeric(s, errors="coerce").dropna()
    if x.empty:
        return {
            "count": 0.0,
            "min": np.nan,
            "p10": np.nan,
            "p25": np.nan,
            "p50": np.nan,
            "p75": np.nan,
            "p90": np.nan,
            "max": np.nan,
            "mean": np.nan,
            "median": np.nan,
            "std": np.nan,
            "cv": np.nan,
        }

    return {
        "count": float(len(x)),
        "min": float(x.min()),
        "p10": float(x.quantile(0.10)),
        "p25": float(x.quantile(0.25)),
        "p50": float(x.quantile(0.50)),
        "p75": float(x.quantile(0.75)),
        "p90": float(x.quantile(0.90)),
        "max": float(x.max()),
        "mean": float(x.mean()),
        "median": float(x.median()),
        "std": float(x.std(ddof=1)),
        "cv": float(x.std(ddof=1) / x.mean()) if x.mean() != 0 else np.nan,
    }


def compare_composites_vs_blocks(
    composites_df: pd.DataFrame,
    block_df: pd.DataFrame,
    value_col: str,
) -> dict[str, dict[str, float]]:
    """Compute basic summary stats for validation-style comparison."""
    return {
        "composites": _series_stats(composites_df[value_col]),
        "blocks": _series_stats(block_df[value_col]),
    }


def format_stats_report(report: dict[str, dict[str, float]], value_col: str) -> str:
    """Return a human-readable plain text report."""
    headers = ["count", "min", "p10", "p25", "p50", "p75", "p90", "max", 
               "mean", "median", "std", "cv"]
    lines: list[str] = []
    lines.append(f"═" * 100)
    lines.append(f"Validation Report: {value_col}")
    lines.append(f"═" * 100)
    
    # Header row
    header_str = "Dataset       |"
    for h in headers:
        header_str += f" {h:>8s} |"
    lines.append(header_str)
    lines.append("─" * 100)

    for label in ["composites", "blocks"]:
        s = report[label]
        row_str = f"{label:<13s}|"
        for h in headers:
            v = s[h]
            if np.isnan(v):
                row_str += f" {'nan':>8s} |"
            elif h == "count":
                row_str += f" {int(v):8d} |"
            else:
                row_str += f" {v:8.3f} |"
        lines.append(row_str)
    
    lines.append(f"═" * 100)
    return "\n".join(lines)


def get_drillhole_statistics(df: pd.DataFrame) -> dict:
    """Compute statistics per drillhole."""
    stats_by_hole: dict = {}
    
    for hole_id, hole_df in df.groupby("hole_id", sort=False):
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        hole_stats = {}
        
        for col in numeric_cols:
            if col in ["x", "y", "z"]:
                continue
            hole_stats[col] = _series_stats(hole_df[col])
        
        # Calculate hole geometry
        coords = hole_df[["x", "y", "z"]].to_numpy()
        if len(coords) > 0:
            deltas = np.linalg.norm(np.diff(coords, axis=0), axis=1)
            hole_stats["hole_length"] = float(np.sum(deltas))
            hole_stats["n_samples"] = len(hole_df)
        
        stats_by_hole[hole_id] = hole_stats
    
    return stats_by_hole


def correlation_analysis(df: pd.DataFrame, numeric_cols: list[str] | None = None) -> pd.DataFrame:
    """Compute correlation matrix for numeric columns."""
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    return df[numeric_cols].corr()


def detect_outliers_iqr(series: pd.Series, k: float = 1.5) -> np.ndarray:
    """Detect outliers using Interquartile Range (IQR) method."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    return (series < lower) | (series > upper)


def get_data_quality_report(df: pd.DataFrame) -> dict:
    """Generate comprehensive data quality report."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Use string type to avoid pandas deprecation warning
    string_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    
    report = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "memory_usage_mb": float(df.memory_usage(deep=True).sum() / 1024**2),
        "missing_values": df.isna().sum().to_dict(),
        "duplicate_rows": len(df) - len(df.drop_duplicates()),
        "numeric_columns": numeric_cols,
        "categorical_columns": string_cols,
    }
    return report

