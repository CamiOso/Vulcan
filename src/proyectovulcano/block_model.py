from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional


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
    estimation_method: str = "idw",
    power: float = 2.0,
    search_radius: float = 25.0,
    max_samples: int = 12,
    variogram_model: str = "spherical",
) -> pd.DataFrame:
    """
    Build a regular block model and estimate value_col by IDW or Kriging.
    
    Parameters:
    -----------
    composites_df : pd.DataFrame
        Input composite data
    value_col : str
        Column name to estimate
    cell_size : tuple
        (dx, dy, dz) block size
    padding : tuple
        (px, py, pz) padding around data
    estimation_method : str
        'idw' (Inverse Distance Weighting) or 'kriging' (Ordinary Kriging)
    power : float
        Power parameter for IDW (default=2)
    search_radius : float
        Search radius for neighbors
    max_samples : int
        Maximum number of neighbors to use
    variogram_model : str
        'spherical' or 'exponential' for kriging
        
    Returns:
    --------
    blocks_df : pd.DataFrame
        Block model with estimates
    """
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

    # Use kriging if requested
    if estimation_method.lower() == "kriging":
        try:
            from .kriging import OrdinaryKriging
            kriging = OrdinaryKriging(valid, value_col)
            records = _build_kriging_blocks(
                x_centers, y_centers, z_centers,
                kriging, value_col, dx, dy, dz
            )
        except ImportError:
            print("Kriging module not available, falling back to IDW")
            records = _build_idw_blocks(
                x_centers, y_centers, z_centers,
                sample_xyz, sample_values, value_col,
                dx, dy, dz, power, search_radius, max_samples
            )
    else:
        records = _build_idw_blocks(
            x_centers, y_centers, z_centers,
            sample_xyz, sample_values, value_col,
            dx, dy, dz, power, search_radius, max_samples
        )

    return pd.DataFrame.from_records(records)


def _build_idw_blocks(
    x_centers: np.ndarray,
    y_centers: np.ndarray,
    z_centers: np.ndarray,
    sample_xyz: np.ndarray,
    sample_values: np.ndarray,
    value_col: str,
    dx: float,
    dy: float,
    dz: float,
    power: float,
    search_radius: float,
    max_samples: int,
) -> list[dict]:
    """Build blocks using IDW estimation"""
    records: list[dict] = []
    for i, x in enumerate(x_centers):
        for j, y in enumerate(y_centers):
            for k, z in enumerate(z_centers):
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
                        "i": int(i),
                        "j": int(j),
                        "k": int(k),
                        "block_id": f"B_{i}_{j}_{k}",
                        "x": float(x),
                        "y": float(y),
                        "z": float(z),
                        "dx": float(dx),
                        "dy": float(dy),
                        "dz": float(dz),
                        value_col: estimate,
                        "n_used": n_used,
                        "method": "IDW",
                    }
                )
    return records


def _build_kriging_blocks(
    x_centers: np.ndarray,
    y_centers: np.ndarray,
    z_centers: np.ndarray,
    kriging,
    value_col: str,
    dx: float,
    dy: float,
    dz: float,
) -> list[dict]:
    """Build blocks using Kriging estimation"""
    records: list[dict] = []
    for i, x in enumerate(x_centers):
        for j, y in enumerate(y_centers):
            for k, z in enumerate(z_centers):
                estimate, variance = kriging.estimate(
                    point=np.array([x, y, z], dtype=float)
                )
                records.append(
                    {
                        "i": int(i),
                        "j": int(j),
                        "k": int(k),
                        "block_id": f"B_{i}_{j}_{k}",
                        "x": float(x),
                        "y": float(y),
                        "z": float(z),
                        "dx": float(dx),
                        "dy": float(dy),
                        "dz": float(dz),
                        value_col: estimate,
                        "kriging_variance": float(variance),
                        "n_used": 1,
                        "method": "Kriging",
                    }
                )
    return records
