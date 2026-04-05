"""
Geostatistics Module - Kriging Interpolation
Implements Ordinary Kriging (OK) with variogram analysis
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from scipy.optimize import minimize
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)


class Variogram:
    """Experimental and theoretical variogram analysis"""

    def __init__(self, df: pd.DataFrame, value_col: str, lag_size: float = 10.0, n_lags: int = 10):
        """
        Initialize variogram calculator

        Parameters:
        -----------
        df : pd.DataFrame
            Input data with x, y, z coordinates
        value_col : str
            Column name for values to analyze
        lag_size : float
            Distance class width (lag size)
        n_lags : int
            Number of lags to calculate
        """
        self.df = df.copy()
        self.value_col = value_col
        self.lag_size = lag_size
        self.n_lags = n_lags
        
        # Extract coordinates
        coords = self.df[['x', 'y', 'z']].values
        values = pd.to_numeric(self.df[value_col], errors='coerce')
        
        # Remove NaN pairs
        valid_idx = values.notna().values
        self.coords = coords[valid_idx]
        self.values = values[valid_idx].values
        
        self.experimental_vario = None
        self.model = None

    def calculate_experimental(self) -> pd.DataFrame:
        """Calculate experimental variogram"""
        n_pairs = len(self.values)
        distances = squareform(pdist(self.coords, metric='euclidean'))
        
        lags = []
        gammas = []
        pairs_count = []
        
        for i in range(self.n_lags):
            lag_min = i * self.lag_size
            lag_max = (i + 1) * self.lag_size
            lag = (lag_min + lag_max) / 2
            
            # Find all pairs within lag distance
            mask = (distances >= lag_min) & (distances < lag_max)
            if np.sum(mask) == 0:
                continue
            
            # Calculate semivariance
            pairs_idx = np.argwhere(mask)
            semivar = 0
            count = 0
            
            for i1, j1 in pairs_idx:
                diff = (self.values[i1] - self.values[j1]) ** 2
                semivar += diff
                count += 1
            
            if count > 0:
                gamma = semivar / (2 * count)
                lags.append(lag)
                gammas.append(gamma)
                pairs_count.append(count)
        
        self.experimental_vario = pd.DataFrame({
            'lag': lags,
            'gamma': gammas,
            'pairs': pairs_count
        })
        
        return self.experimental_vario

    def fit_spherical(self) -> dict:
        """Fit spherical model to experimental variogram"""
        if self.experimental_vario is None:
            self.calculate_experimental()
        
        lags = self.experimental_vario['lag'].values
        gammas = self.experimental_vario['gamma'].values
        
        # Initial guess
        nugget = gammas.min() * 0.1
        sill = gammas.max()
        range_param = lags.max() / 3
        
        def spherical(params, h):
            nug, sill, rng = params
            h = np.asarray(h)
            result = np.zeros_like(h, dtype=float)
            
            within_range = h <= rng
            result[within_range] = nug + (sill - nug) * (
                1.5 * (h[within_range] / rng) - 0.5 * (h[within_range] / rng) ** 3
            )
            result[~within_range] = sill
            
            return result
        
        def objective(params):
            predicted = spherical(params, lags)
            return np.sum((gammas - predicted) ** 2)
        
        result = minimize(
            objective,
            [nugget, sill, range_param],
            bounds=[(0, None), (nugget, None), (0.1, None)],
            method='L-BFGS-B'
        )
        
        self.model = {
            'type': 'spherical',
            'nugget': result.x[0],
            'sill': result.x[1],
            'range': result.x[2]
        }
        
        return self.model

    def fit_exponential(self) -> dict:
        """Fit exponential model to experimental variogram"""
        if self.experimental_vario is None:
            self.calculate_experimental()
        
        lags = self.experimental_vario['lag'].values
        gammas = self.experimental_vario['gamma'].values
        
        nugget = gammas.min() * 0.1
        sill = gammas.max()
        range_param = lags.max() / 3
        
        def exponential(params, h):
            nug, sill, rng = params
            h = np.asarray(h, dtype=float)
            return nug + (sill - nug) * (1 - np.exp(-3 * h / rng))
        
        def objective(params):
            predicted = exponential(params, lags)
            return np.sum((gammas - predicted) ** 2)
        
        result = minimize(
            objective,
            [nugget, sill, range_param],
            bounds=[(0, None), (nugget, None), (0.1, None)],
            method='L-BFGS-B'
        )
        
        self.model = {
            'type': 'exponential',
            'nugget': result.x[0],
            'sill': result.x[1],
            'range': result.x[2]
        }
        
        return self.model

    def gamma(self, h: float) -> float:
        """Calculate semivariance at distance h"""
        if self.model is None:
            self.fit_spherical()
        
        model = self.model
        nug, sill, rng = model['nugget'], model['sill'], model['range']
        
        if model['type'] == 'spherical':
            if h <= rng:
                return nug + (sill - nug) * (1.5 * (h / rng) - 0.5 * (h / rng) ** 3)
            else:
                return sill
        elif model['type'] == 'exponential':
            return nug + (sill - nug) * (1 - np.exp(-3 * h / rng))


class OrdinaryKriging:
    """Ordinary Kriging interpolator"""

    def __init__(self, df: pd.DataFrame, value_col: str, variogram: Variogram = None):
        """
        Initialize kriging estimator

        Parameters:
        -----------
        df : pd.DataFrame
            Training data with x, y, z coordinates
        value_col : str
            Column name for values
        variogram : Variogram
            Pre-fitted variogram (optional)
        """
        self.df = df.copy()
        self.value_col = value_col
        
        # Extract valid data
        valid_idx = pd.to_numeric(self.df[value_col], errors='coerce').notna()
        self.coords = self.df.loc[valid_idx, ['x', 'y', 'z']].values
        self.values = pd.to_numeric(self.df.loc[valid_idx, value_col], errors='coerce').values
        
        # Fit variogram if not provided
        if variogram is None:
            self.variogram = Variogram(self.df, value_col)
            self.variogram.fit_spherical()
        else:
            self.variogram = variogram

    def estimate(self, point: tuple, search_radius: float = 50.0, max_neighbors: int = 16) -> tuple:
        """
        Estimate value at a point using OK

        Parameters:
        -----------
        point : tuple
            (x, y, z) coordinates
        search_radius : float
            Search radius for neighbors
        max_neighbors : int
            Maximum number of neighbors to use

        Returns:
        --------
        estimate : float
            Estimated value
        variance : float
            Kriging variance
        """
        point = np.asarray(point)
        
        # Find neighbors within search radius
        distances = np.linalg.norm(self.coords - point, axis=1)
        neighbor_idx = np.argsort(distances)[:max_neighbors]
        neighbor_idx = neighbor_idx[distances[neighbor_idx] <= search_radius]
        
        if len(neighbor_idx) < 3:
            # Fallback to inverse distance weighting if not enough neighbors
            if len(neighbor_idx) == 0:
                neighbor_idx = np.argsort(distances)[:max_neighbors]
            d = distances[neighbor_idx]
            if np.any(d == 0):
                return float(self.values[neighbor_idx[d == 0]][0]), 0.0
            weights = 1 / (d ** 2)
            weights /= weights.sum()
            return float(np.sum(self.values[neighbor_idx] * weights)), np.var(self.values[neighbor_idx])
        
        # Build kriging system
        n = len(neighbor_idx)
        K = np.zeros((n + 1, n + 1))
        
        # Semivariogram matrix
        neighbor_coords = self.coords[neighbor_idx]
        for i in range(n):
            for j in range(n):
                h = np.linalg.norm(neighbor_coords[i] - neighbor_coords[j])
                K[i, j] = self.variogram.gamma(h)
        
        # Add constraint for OK
        K[n, :n] = 1
        K[:n, n] = 1
        K[n, n] = 0
        
        # Right-hand side
        b = np.zeros(n + 1)
        for i in range(n):
            h = np.linalg.norm(neighbor_coords[i] - point)
            b[i] = self.variogram.gamma(h)
        b[n] = 1
        
        # Solve system
        try:
            weights = np.linalg.solve(K, b)
        except np.linalg.LinAlgError:
            # Fallback to least squares if singular
            weights = np.linalg.lstsq(K, b, rcond=None)[0]
        
        # Calculate estimate
        estimate = np.sum(weights[:n] * self.values[neighbor_idx])
        
        # Calculate variance
        variance = np.sum(weights[:n] * b[:n])
        
        return float(estimate), float(variance)

    def estimate_grid(self, grid_coords: np.ndarray, search_radius: float = 50.0, 
                      max_neighbors: int = 16) -> tuple:
        """
        Estimate values on a regular grid

        Parameters:
        -----------
        grid_coords : np.ndarray
            Array of (x, y, z) coordinates
        search_radius : float
            Search radius for neighbors
        max_neighbors : int
            Maximum number of neighbors

        Returns:
        --------
        estimates : np.ndarray
            Estimated values
        variances : np.ndarray
            Kriging variances
        """
        estimates = []
        variances = []
        
        for coord in grid_coords:
            est, var = self.estimate(coord, search_radius, max_neighbors)
            estimates.append(est)
            variances.append(var)
        
        return np.array(estimates), np.array(variances)


class KrigingGridBuilder:
    """Build kriged grid model similar to IDW"""

    def __init__(self, composites_df: pd.DataFrame, value_col: str = 'au',
                 model_type: str = 'spherical'):
        """
        Initialize kriging grid builder

        Parameters:
        -----------
        composites_df : pd.DataFrame
            Composite data
        value_col : str
            Value column
        model_type : str
            Variogram model ('spherical', 'exponential')
        """
        self.composites_df = composites_df
        self.value_col = value_col
        self.model_type = model_type
        
        # Fit variogram
        self.variogram = Variogram(composites_df, value_col)
        if model_type == 'spherical':
            self.variogram.fit_spherical()
        else:
            self.variogram.fit_exponential()
        
        # Initialize kriging estimator
        self.kriging = OrdinaryKriging(composites_df, value_col, self.variogram)

    def build_kriged_model(self, grid_size: tuple = (10, 10, 5), padding: tuple = (0, 0, 0)) -> pd.DataFrame:
        """
        Build kriged grid model

        Parameters:
        -----------
        grid_size : tuple
            (dx, dy, dz) grid size
        padding : tuple
            (px, py, pz) padding around data

        Returns:
        --------
        blocks_df : pd.DataFrame
            Kriged block model
        """
        dx, dy, dz = grid_size
        px, py, pz = padding
        
        # Define grid bounds
        x_min = self.composites_df['x'].min() - px
        x_max = self.composites_df['x'].max() + px
        y_min = self.composites_df['y'].min() - py
        y_max = self.composites_df['y'].max() + py
        z_min = self.composites_df['z'].min() - pz
        z_max = self.composites_df['z'].max() + pz
        
        # Generate grid
        x_centers = np.arange(x_min + dx/2, x_max, dx)
        y_centers = np.arange(y_min + dy/2, y_max, dy)
        z_centers = np.arange(z_min + dz/2, z_max, dz)
        
        n_x, n_y, n_z = len(x_centers), len(y_centers), len(z_centers)
        
        blocks = []
        block_id = 0
        
        for k, z in enumerate(z_centers):
            for j, y in enumerate(y_centers):
                for i, x in enumerate(x_centers):
                    coord = np.array([x, y, z])
                    
                    # Estimate using kriging
                    estimate, variance = self.kriging.estimate(coord)
                    
                    blocks.append({
                        'i': i,
                        'j': j,
                        'k': k,
                        'block_id': block_id,
                        'x': x,
                        'y': y,
                        'z': z,
                        'dx': dx,
                        'dy': dy,
                        'dz': dz,
                        self.value_col: estimate,
                        'kriging_variance': variance,
                        'n_used': 1  # OK uses multiple neighbors, simplified here
                    })
                    
                    block_id += 1
        
        blocks_df = pd.DataFrame(blocks)
        return blocks_df


def kriging_estimate(df: pd.DataFrame, grid_size: tuple = (10, 10, 5), 
                     value_col: str = 'au', model_type: str = 'spherical',
                     padding: tuple = (0, 0, 0)) -> pd.DataFrame:
    """
    Convenience function to build kriged grid model

    Parameters:
    -----------
    df : pd.DataFrame
        Input composites
    grid_size : tuple
        (dx, dy, dz)
    value_col : str
        Value column
    model_type : str
        'spherical' or 'exponential'
    padding : tuple
        (px, py, pz)

    Returns:
    --------
    blocks : pd.DataFrame
        Kriged block model
    """
    builder = KrigingGridBuilder(df, value_col, model_type)
    return builder.build_kriged_model(grid_size, padding)
