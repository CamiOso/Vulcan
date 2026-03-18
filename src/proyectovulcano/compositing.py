from __future__ import annotations

import numpy as np
import pandas as pd


def _compute_depth_along_hole(hole_df: pd.DataFrame) -> np.ndarray:
    """Return downhole depth for each sample, using `depth` if available."""
    if "depth" in hole_df.columns:
        return hole_df["depth"].to_numpy(dtype=float)

    xyz = hole_df[["x", "y", "z"]].to_numpy(dtype=float)
    if len(xyz) == 0:
        return np.array([], dtype=float)

    deltas = np.linalg.norm(np.diff(xyz, axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(deltas)])


def composite_drillholes(
    df: pd.DataFrame,
    value_col: str,
    composite_length: float = 10.0,
) -> pd.DataFrame:
    """Create fixed-length composites per hole_id."""
    if composite_length <= 0:
        raise ValueError("composite_length must be > 0")
    if value_col not in df.columns:
        raise ValueError(f"Column not found for compositing: {value_col}")

    records: list[dict] = []

    for hole_id, hole_df in df.groupby("hole_id", sort=False):
        if "depth" in hole_df.columns:
            ordered = hole_df.sort_values("depth", ascending=True).copy()
        else:
            ordered = hole_df.sort_values("z", ascending=False).copy()

        ordered[value_col] = pd.to_numeric(ordered[value_col], errors="coerce")
        ordered = ordered.dropna(subset=[value_col, "x", "y", "z"])
        if ordered.empty:
            continue

        depth = _compute_depth_along_hole(ordered)
        ordered = ordered.assign(_depth=depth)

        comp_idx = np.floor(ordered["_depth"] / composite_length).astype(int)
        ordered = ordered.assign(_comp=comp_idx)

        grouped = ordered.groupby("_comp", sort=True)
        for comp, comp_df in grouped:
            depth_min = float(comp * composite_length)
            depth_max = float((comp + 1) * composite_length)
            records.append(
                {
                    "hole_id": hole_id,
                    "comp_from": depth_min,
                    "comp_to": depth_max,
                    "x": float(comp_df["x"].mean()),
                    "y": float(comp_df["y"].mean()),
                    "z": float(comp_df["z"].mean()),
                    value_col: float(comp_df[value_col].mean()),
                    "n_samples": int(len(comp_df)),
                }
            )

    if not records:
        return pd.DataFrame(
            columns=[
                "hole_id",
                "comp_from",
                "comp_to",
                "x",
                "y",
                "z",
                value_col,
                "n_samples",
            ]
        )

    return pd.DataFrame.from_records(records)
