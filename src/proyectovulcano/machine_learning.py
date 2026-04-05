"""
Machine Learning Module - Estimation with Regression Models
Implements Linear Regression, Random Forest, and Gradient Boosting for variable estimation
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional, Tuple, List
import warnings

warnings.filterwarnings('ignore', category=UserWarning)

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, cross_validate
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error


class FeatureEngineer:
    """Feature engineering for ML estimation"""

    def __init__(self, df: pd.DataFrame, target_col: str, feature_cols: Optional[List[str]] = None):
        """
        Initialize feature engineer

        Parameters:
        -----------
        df : pd.DataFrame
            Input data
        target_col : str
            Target column to estimate
        feature_cols : Optional[List[str]]
            Feature columns (auto-detect if None)
        """
        self.df = df.copy()
        self.target_col = target_col
        
        # Auto-detect numeric features (excluding target)
        if feature_cols is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            self.feature_cols = [col for col in numeric_cols if col != target_col]
        else:
            self.feature_cols = feature_cols
        
        self.scaler = None
        self.X = None
        self.y = None
        self._prepare_data()

    def _prepare_data(self) -> None:
        """Prepare and clean data"""
        # Select features and target
        data = self.df[self.feature_cols + [self.target_col]].copy()
        
        # Remove NaN values
        data = data.dropna()
        
        if len(data) == 0:
            raise ValueError("No valid data after removing NaNs")
        
        self.X = data[self.feature_cols].values
        self.y = data[self.target_col].values

    def normalize(self) -> Tuple[np.ndarray, np.ndarray]:
        """Normalize features using StandardScaler"""
        self.scaler = StandardScaler()
        self.X = self.scaler.fit_transform(self.X)
        return self.X, self.y

    def get_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Get processed data"""
        return self.X, self.y, self.feature_cols


class RegressionEstimator:
    """Base class for regression estimators"""

    def __init__(
        self, 
        model_type: str = 'linear', 
        normalize: bool = True,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        learning_rate: float = 0.1
    ):
        """
        Initialize estimator

        Parameters:
        -----------
        model_type : str
            'linear', 'rf' (random forest), or 'gb' (gradient boosting)
        normalize : bool
            Normalize features
        n_estimators : int
            Number of estimators (for RF and GB)
        max_depth : Optional[int]
            Maximum depth of trees
        learning_rate : float
            Learning rate (for GB)
        """
        self.model_type = model_type
        self.normalize = normalize
        self.n_estimators = n_estimators
        self.max_depth = max_depth if max_depth is not None else (15 if model_type == 'rf' else 5)
        self.learning_rate = learning_rate
        self.model = None
        self.engineer = None
        self.scaler = None
        self.feature_importance = None
        self._build_model()

    def _build_model(self) -> None:
        """Build the model"""
        if self.model_type == 'linear':
            self.model = LinearRegression()
        elif self.model_type == 'rf':
            self.model = RandomForestRegressor(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gb':
            self.model = GradientBoostingRegressor(
                n_estimators=self.n_estimators,
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def fit(self, df: pd.DataFrame, target_col: str, 
            feature_cols: Optional[List[str]] = None) -> None:
        """
        Fit model on training data

        Parameters:
        -----------
        df : pd.DataFrame
            Training data
        target_col : str
            Target column
        feature_cols : Optional[List[str]]
            Feature columns
        """
        # Prepare data
        self.engineer = FeatureEngineer(df, target_col, feature_cols)
        X, y, self.feature_cols = self.engineer.get_data()
        
        # Normalize if requested
        if self.normalize:
            X, y = self.engineer.normalize()
            self.scaler = self.engineer.scaler
        
        # Fit model
        self.model.fit(X, y)
        
        # Extract feature importance for tree-based models
        if self.model_type in ['rf', 'gb']:
            self.feature_importance = dict(zip(self.feature_cols, self.model.feature_importances_))

    def predict(self, X_new: np.ndarray) -> np.ndarray:
        """
        Make predictions

        Parameters:
        -----------
        X_new : np.ndarray
            New data (n_samples, n_features)

        Returns:
        --------
        predictions : np.ndarray
            Predicted values
        """
        if self.scaler is not None:
            X_new = self.scaler.transform(X_new)
        
        return self.model.predict(X_new)

    def predict_dataframe(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict from dataframe

        Parameters:
        -----------
        df : pd.DataFrame
            Data with features matching training data

        Returns:
        --------
        predictions : np.ndarray
            Predicted values
        """
        X = df[self.feature_cols].values
        return self.predict(X)

    def cross_validate(self, X: np.ndarray, y: np.ndarray, cv: int = 5) -> dict:
        """
        Cross-validate model

        Parameters:
        -----------
        X : np.ndarray
            Features
        y : np.ndarray
            Target
        cv : int
            Number of folds

        Returns:
        --------
        scores : dict
            Cross-validation scores
        """
        scoring = {
            'r2': 'r2',
            'neg_mse': 'neg_mean_squared_error',
            'neg_mae': 'neg_mean_absolute_error'
        }
        
        scores = cross_validate(self.model, X, y, cv=cv, scoring=scoring)
        
        return {
            'r2_mean': scores['test_r2'].mean(),
            'r2_std': scores['test_r2'].std(),
            'rmse_mean': np.sqrt(-scores['test_neg_mse'].mean()),
            'rmse_std': np.sqrt(scores['test_neg_mse'].std()),
            'mae_mean': -scores['test_neg_mae'].mean(),
            'mae_std': scores['test_neg_mae'].std(),
        }

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """
        Evaluate on test set

        Parameters:
        -----------
        X_test : np.ndarray
            Test features
        y_test : np.ndarray
            Test target

        Returns:
        --------
        metrics : dict
            Evaluation metrics
        """
        y_pred = self.predict(X_test)
        
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        
        return {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'mape': mape
        }

    def get_feature_importance(self) -> dict:
        """Get feature importance (tree-based models only)"""
        if self.feature_importance is None:
            return {}
        return self.feature_importance


class MultiVariableEstimator:
    """Estimate multiple target variables with ML"""

    def __init__(self, df: pd.DataFrame, target_cols: List[str], 
                 model_type: str = 'rf', normalize: bool = True):
        """
        Initialize multi-variable estimator

        Parameters:
        -----------
        df : pd.DataFrame
            Training data
        target_cols : List[str]
            Target columns to estimate
        model_type : str
            Model type ('linear', 'rf', 'gb')
        normalize : bool
            Normalize features
        """
        self.df = df
        self.target_cols = target_cols
        self.model_type = model_type
        self.normalize = normalize
        self.models: dict[str, RegressionEstimator] = {}
        
        # Fit models for each target
        for target_col in target_cols:
            model = RegressionEstimator(model_type, normalize)
            model.fit(df, target_col)
            self.models[target_col] = model

    def predict(self, X_new: pd.DataFrame) -> pd.DataFrame:
        """
        Predict all targets

        Parameters:
        -----------
        X_new : pd.DataFrame
            New data

        Returns:
        --------
        predictions : pd.DataFrame
            Predicted values for all targets
        """
        predictions = {}
        for target_col, model in self.models.items():
            predictions[target_col] = model.predict_dataframe(X_new)
        
        return pd.DataFrame(predictions)


class MLBlockModelBuilder:
    """Build block model using Machine Learning"""

    def __init__(self, composites_df: pd.DataFrame, target_col: str = 'au',
                 model_type: str = 'rf', feature_cols: Optional[List[str]] = None):
        """
        Initialize ML block builder

        Parameters:
        -----------
        composites_df : pd.DataFrame
            Training composites
        target_col : str
            Target value column
        model_type : str
            Model type ('linear', 'rf', 'gb')
        feature_cols : Optional[List[str]]
            Feature columns (auto-detect if None)
        """
        self.composites_df = composites_df
        self.target_col = target_col
        self.model_type = model_type
        
        # Fit model
        self.estimator = RegressionEstimator(model_type, normalize=True)
        self.estimator.fit(composites_df, target_col, feature_cols)

    def build_ml_model(self, grid_coords: np.ndarray) -> pd.DataFrame:
        """
        Build ML block model

        Parameters:
        -----------
        grid_coords : np.ndarray
            Grid coordinates (n_blocks, n_features)

        Returns:
        --------
        blocks_df : pd.DataFrame
            Block model with ML estimates
        """
        # Make predictions
        predictions = self.estimator.predict(grid_coords)
        
        # Create blocks dataframe
        blocks = pd.DataFrame({
            'estimate': predictions,
            'model': self.model_type,
            'method': 'MachineLearning'
        })
        
        return blocks


def estimate_with_ml(df: pd.DataFrame, grid_size: tuple = (10, 10, 5),
                     target_col: str = 'au', model_type: str = 'rf',
                     padding: tuple = (0, 0, 0)) -> pd.DataFrame:
    """
    Convenience function to estimate block model with ML

    Parameters:
    -----------
    df : pd.DataFrame
        Input composites
    grid_size : tuple
        (dx, dy, dz)
    target_col : str
        Target column
    model_type : str
        'linear', 'rf', or 'gb'
    padding : tuple
        (px, py, pz)

    Returns:
    --------
    blocks : pd.DataFrame
        ML-estimated block model
    """
    from src.proyectovulcano.block_model import _axis_centers
    
    dx, dy, dz = grid_size
    px, py, pz = padding
    
    # Get valid data
    valid_df = df[['x', 'y', 'z', target_col]].copy()
    valid_df[target_col] = pd.to_numeric(valid_df[target_col], errors='coerce')
    valid_df = valid_df.dropna()
    
    # Define grid
    x_min = valid_df['x'].min() - px
    x_max = valid_df['x'].max() + px
    y_min = valid_df['y'].min() - py
    y_max = valid_df['y'].max() + py
    z_min = valid_df['z'].min() - pz
    z_max = valid_df['z'].max() + pz
    
    x_centers = _axis_centers(x_min, x_max, dx)
    y_centers = _axis_centers(y_min, y_max, dy)
    z_centers = _axis_centers(z_min, z_max, dz)
    
    # Get features for ML
    feature_cols = [col for col in df.columns if col not in ['x', 'y', 'z', target_col, 'hole_id']]
    
    blocks = []
    block_id = 0
    
    for k, z in enumerate(z_centers):
        for j, y in enumerate(y_centers):
            for i, x in enumerate(x_centers):
                # Use coordinate features
                coords = np.array([[x, y, z]])
                
                # Build features from training data
                if len(feature_cols) > 0:
                    X_features = valid_df[feature_cols].mean(axis=0).values.reshape(1, -1)
                    X_input = np.hstack([coords, X_features])
                else:
                    X_input = coords
                
                # Fit model on training data for this estimation
                try:
                    estimator = RegressionEstimator(model_type, normalize=True)
                    estimator.fit(valid_df, target_col, ['x', 'y', 'z'] + feature_cols)
                    estimate = estimator.predict(X_input)[0]
                except:
                    # Fallback to mean if model fails
                    estimate = valid_df[target_col].mean()
                
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
                    target_col: estimate,
                    'method': 'ML',
                    'model': model_type
                })
                
                block_id += 1
    
    return pd.DataFrame(blocks)
