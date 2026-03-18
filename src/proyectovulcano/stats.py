from __future__ import annotations

import numpy as np
import pandas as pd


def _series_stats(s: pd.Series) -> dict[str, float]:
    x = pd.to_numeric(s, errors="coerce").dropna()
    if x.empty:
        return {
            "count": 0.0,
            "min": np.nan,
            "p10": np.nan,
            "p50": np.nan,
            "p90": np.nan,
            "max": np.nan,
            "mean": np.nan,
            "std": np.nan,
        }

    return {
        "count": float(len(x)),
        "min": float(x.min()),
        "p10": float(x.quantile(0.10)),
        "p50": float(x.quantile(0.50)),
        "p90": float(x.quantile(0.90)),
        "max": float(x.max()),
        "mean": float(x.mean()),
        "std": float(x.std(ddof=0)),
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
    headers = ["count", "min", "p10", "p50", "p90", "max", "mean", "std"]
    lines: list[str] = []
    lines.append(f"Validation report for: {value_col}")
    lines.append("dataset      " + "  ".join(f"{h:>8s}" for h in headers))

    for label in ["composites", "blocks"]:
        s = report[label]
        parts = []
        for h in headers:
            v = s[h]
            if np.isnan(v):
                parts.append(f"{'nan':>8s}")
            elif h == "count":
                parts.append(f"{int(v):8d}")
            else:
                parts.append(f"{v:8.3f}")
        lines.append(f"{label:<12s}" + "  ".join(parts))

    return "\n".join(lines)
