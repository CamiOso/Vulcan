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
    ml_model_type: str = "rf",
    grid_size: tuple[float, float, float] = None,
    ml_params: dict = None,
) -> pd.DataFrame:
    """
    Build a regular block model and estimate value_col by IDW, Kriging, or ML.
    
    Parameters:
    -----------
    composites_df : pd.DataFrame
        Input composite data
    value_col : str
        Column name to estimate
    cell_size : tuple
        (dx, dy, dz) block size (or use grid_size parameter)
    padding : tuple
        (px, py, pz) padding around data
    estimation_method : str
        'idw' (Inverse Distance Weighting), 'kriging' (Ordinary Kriging), 
        'linear' (Linear Regression), 'rf' (Random Forest), or 'gb' (Gradient Boosting)
    power : float
        Power parameter for IDW (default=2)
    search_radius : float
        Search radius for neighbors
    max_samples : int
        Maximum number of neighbors to use
    variogram_model : str
        'spherical' or 'exponential' for kriging
    ml_model_type : str
        'linear', 'rf' (Random Forest), or 'gb' (Gradient Boosting) for ML (deprecated, use estimation_method)
    grid_size : tuple
        Alternative name for cell_size (for GUI compatibility)
    ml_params : dict
        Additional ML parameters (normalize, cv_folds, n_estimators, max_depth, learning_rate)
        
    Returns:
    --------
    blocks_df : pd.DataFrame
        Block model with estimates
    """
    # Handle grid_size as alias for cell_size
    if grid_size is not None:
        cell_size = grid_size
    
    # Set default ml_params
    if ml_params is None:
        ml_params = {}
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

    # Determine if ML method
    ml_methods = {"linear", "rf", "gb"}
    method_lower = estimation_method.lower().replace("_", "")
    is_ml_method = method_lower in ml_methods
    
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
    elif is_ml_method or estimation_method.lower() == "ml":
        try:
            from .machine_learning import RegressionEstimator
            # Use estimation_method if it's a valid ML method, otherwise use ml_model_type
            model_type = method_lower if is_ml_method else ml_model_type
            records = _build_ml_blocks(
                x_centers, y_centers, z_centers,
                valid, value_col, dx, dy, dz, model_type, ml_params
            )
        except ImportError:
            print("Machine Learning module not available, falling back to IDW")
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


def _build_ml_blocks(
    x_centers: np.ndarray,
    y_centers: np.ndarray,
    z_centers: np.ndarray,
    composites: pd.DataFrame,
    value_col: str,
    dx: float,
    dy: float,
    dz: float,
    model_type: str = "rf",
    ml_params: dict = None,
) -> list[dict]:
    """Build blocks using Machine Learning estimation"""
    from .machine_learning import RegressionEstimator
    
    if ml_params is None:
        ml_params = {}
    
    # Extract ML parameters with defaults
    normalize = ml_params.get("normalize", True)
    cv_folds = ml_params.get("cv_folds", 5)
    n_estimators = ml_params.get("n_estimators", 100)
    max_depth = ml_params.get("max_depth", 10)
    learning_rate = ml_params.get("learning_rate", 0.1)
    
    # Fit ML model
    estimator = RegressionEstimator(
        model_type, 
        normalize=normalize,
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate
    )
    estimator.fit(composites, value_col)
    
    records: list[dict] = []
    for i, x in enumerate(x_centers):
        for j, y in enumerate(y_centers):
            for k, z in enumerate(z_centers):
                # Create feature array: coordinate + average of other numeric features
                coord = np.array([[x, y, z]])
                
                # Get other numeric features if available
                feature_cols = estimator.feature_cols
                if len(feature_cols) > 3:  # More than just x, y, z
                    other_features = composites[feature_cols[3:]].mean().values.reshape(1, -1)
                    X_input = np.hstack([coord, other_features])
                else:
                    X_input = coord
                
                # Predict
                try:
                    estimate = float(estimator.predict(X_input)[0])
                except:
                    estimate = composites[value_col].mean()
                
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
                        "n_used": 1,
                        "method": "ML",
                        "ml_model": model_type,
                    }
                )
    return records
