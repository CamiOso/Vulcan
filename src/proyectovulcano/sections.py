from __future__ import annotations

import pandas as pd


def extract_section(
    df: pd.DataFrame,
    section_type: str,
    center: float | None,
    width: float,
) -> tuple[pd.DataFrame, dict[str, float | str]]:
    """Extract a 2D section window from 3D points."""
    if width <= 0:
        raise ValueError("section width must be > 0")
    if section_type not in {"longitudinal", "transversal"}:
        raise ValueError("section_type must be 'longitudinal' or 'transversal'")

    if section_type == "longitudinal":
        orth_col = "x"
        horiz_col = "y"
        horiz_label = "Y"
    else:
        orth_col = "y"
        horiz_col = "x"
        horiz_label = "X"

    use_center = float(df[orth_col].mean()) if center is None else float(center)
    half = width / 2.0
    mask = (df[orth_col] >= use_center - half) & (df[orth_col] <= use_center + half)
    section_df = df.loc[mask].copy()

    meta: dict[str, float | str] = {
        "section_type": section_type,
        "orth_col": orth_col,
        "horiz_col": horiz_col,
        "horiz_label": horiz_label,
        "center": use_center,
        "width": float(width),
    }
    return section_df, meta
