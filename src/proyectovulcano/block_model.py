from __future__ import annotations

import numpy as np
import pandas as pd


def _axis_centers(min_val: float, max_val: float, cell: float) -> np.ndarray:
    start = min_val + cell / 2.0
    stop = max_val - cell / 2.0
    if stop < start:
        return np.array([start], dtype=float)
    count = int(np.floor((stop - start) / cell)) + 1
    return start + np.arange(count, dtype=float) * cell


def _idw_estimate(
    sample_xyz: np.ndarray,
    sample_values: np.ndarray,
    query_point: np.ndarray,
    power: float,
    search_radius: float,
    max_samples: int,
) -> tuple[float, int]:
    distances = np.linalg.norm(sample_xyz - query_point, axis=1)

    if search_radius > 0:
        mask = distances <= search_radius
        distances = distances[mask]
        values = sample_values[mask]
    else:
        values = sample_values

    if len(distances) == 0:
        return np.nan, 0

    order = np.argsort(distances)
    if max_samples > 0:
        order = order[:max_samples]

    distances = distances[order]
    values = values[order]

    if np.any(distances == 0):
        return float(values[distances == 0][0]), int(len(values))

    weights = 1.0 / np.power(distances, power)
    estimate = float(np.sum(weights * values) / np.sum(weights))
    return estimate, int(len(values))


def build_regular_block_model(
    composites_df: pd.DataFrame,
    value_col: str,
    cell_size: tuple[float, float, float] = (10.0, 10.0, 5.0),
    padding: tuple[float, float, float] = (0.0, 0.0, 0.0),
    power: float = 2.0,
    search_radius: float = 25.0,
    max_samples: int = 12,
) -> pd.DataFrame:
    """Build a regular block model and estimate value_col by IDW."""
    if value_col not in composites_df.columns:
        raise ValueError(f"Column not found for estimation: {value_col}")

    valid = composites_df[["x", "y", "z", value_col]].copy()
    valid[value_col] = pd.to_numeric(valid[value_col], errors="coerce")
    valid = valid.dropna(subset=["x", "y", "z", value_col])
    if valid.empty:
        raise ValueError("No valid composites available for block estimation")

    dx, dy, dz = cell_size
    px, py, pz = padding
    if dx <= 0 or dy <= 0 or dz <= 0:
        raise ValueError("cell_size values must be > 0")

    min_x, max_x = float(valid["x"].min() - px), float(valid["x"].max() + px)
    min_y, max_y = float(valid["y"].min() - py), float(valid["y"].max() + py)
    min_z, max_z = float(valid["z"].min() - pz), float(valid["z"].max() + pz)

    x_centers = _axis_centers(min_x, max_x, dx)
    y_centers = _axis_centers(min_y, max_y, dy)
    z_centers = _axis_centers(min_z, max_z, dz)

    sample_xyz = valid[["x", "y", "z"]].to_numpy(dtype=float)
    sample_values = valid[value_col].to_numpy(dtype=float)

    records: list[dict] = []
    for x in x_centers:
        for y in y_centers:
            for z in z_centers:
                estimate, n_used = _idw_estimate(
                    sample_xyz=sample_xyz,
                    sample_values=sample_values,
                    query_point=np.array([x, y, z], dtype=float),
                    power=power,
                    search_radius=search_radius,
                    max_samples=max_samples,
                )
                records.append(
                    {
                        "x": float(x),
                        "y": float(y),
                        "z": float(z),
                        "dx": float(dx),
                        "dy": float(dy),
                        "dz": float(dz),
                        value_col: estimate,
                        "n_used": n_used,
                    }
                )

    return pd.DataFrame.from_records(records)
