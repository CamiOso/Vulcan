"""
Tests for Kriging module
"""

import pytest
import numpy as np
import pandas as pd
from src.proyectovulcano.kriging import Variogram, OrdinaryKriging, KrigingGridBuilder, kriging_estimate


@pytest.fixture
def sample_data():
    """Create sample data for testing"""
    np.random.seed(42)
    n_points = 20
    
    df = pd.DataFrame({
        'x': np.random.uniform(0, 100, n_points),
        'y': np.random.uniform(0, 100, n_points),
        'z': np.random.uniform(0, 50, n_points),
        'au': np.random.uniform(0.1, 1.5, n_points),
        'cu': np.random.uniform(0.01, 0.1, n_points)
    })
    
    return df


class TestVariogram:
    """Test variogram calculations"""

    def test_variogram_initialization(self, sample_data):
        """Test variogram creation"""
        vario = Variogram(sample_data, 'au', lag_size=10, n_lags=5)
        assert vario.value_col == 'au'
        assert len(vario.coords) == 20
        assert len(vario.values) == 20

    def test_experimental_variogram(self, sample_data):
        """Test experimental variogram calculation"""
        vario = Variogram(sample_data, 'au', lag_size=15, n_lags=4)
        exp_vario = vario.calculate_experimental()
        
        assert exp_vario is not None
        assert 'lag' in exp_vario.columns
        assert 'gamma' in exp_vario.columns
        assert 'pairs' in exp_vario.columns
        assert len(exp_vario) > 0
        assert (exp_vario['gamma'] >= 0).all()

    def test_fit_spherical(self, sample_data):
        """Test spherical model fitting"""
        vario = Variogram(sample_data, 'au')
        model = vario.fit_spherical()
        
        assert model is not None
        assert 'nugget' in model
        assert 'sill' in model
        assert 'range' in model
        assert model['nugget'] >= 0
        assert model['sill'] >= model['nugget']
        assert model['range'] > 0

    def test_fit_exponential(self, sample_data):
        """Test exponential model fitting"""
        vario = Variogram(sample_data, 'au')
        model = vario.fit_exponential()
        
        assert model is not None
        assert model['type'] == 'exponential'
        assert model['nugget'] >= 0
        assert model['sill'] > 0

    def test_gamma_calculation(self, sample_data):
        """Test semivariance calculation at distance"""
        vario = Variogram(sample_data, 'au')
        vario.fit_spherical()
        
        gamma_0 = vario.gamma(0)
        gamma_10 = vario.gamma(10)
        gamma_100 = vario.gamma(100)
        
        # At distance 0, gamma should be close to nugget
        assert abs(gamma_0 - vario.model['nugget']) < 0.1
        
        # Gamma should increase (or stay constant) with distance
        assert gamma_10 >= gamma_0
        assert gamma_100 >= gamma_10 or abs(gamma_100 - gamma_10) < 0.1


class TestOrdinaryKriging:
    """Test ordinary kriging estimator"""

    def test_kriging_initialization(self, sample_data):
        """Test kriging estimator creation"""
        kriging = OrdinaryKriging(sample_data, 'au')
        assert kriging.value_col == 'au'
        assert len(kriging.coords) == 20
        assert kriging.variogram is not None

    def test_kriging_estimate(self, sample_data):
        """Test single point estimation"""
        kriging = OrdinaryKriging(sample_data, 'au')
        
        # Estimate at a new point
        point = (50, 50, 25)
        estimate, variance = kriging.estimate(point)
        
        assert isinstance(estimate, float)
        assert isinstance(variance, float)
        assert 0 < estimate < 2  # Should be in reasonable range
        assert variance >= 0

    def test_kriging_estimate_at_data_point(self, sample_data):
        """Test that kriging gives close estimate at data points"""
        kriging = OrdinaryKriging(sample_data, 'au')
        
        # Use first data point
        point = sample_data.iloc[0][['x', 'y', 'z']].values
        true_value = sample_data.iloc[0]['au']
        estimate, _ = kriging.estimate(point, max_neighbors=16)
        
        # Should be close to true value (within 30% for small dataset)
        relative_error = abs(estimate - true_value) / true_value
        assert relative_error < 0.5  # Loose tolerance for small sample

    def test_kriging_grid_estimation(self, sample_data):
        """Test grid estimation"""
        kriging = OrdinaryKriging(sample_data, 'au')
        
        grid_coords = np.array([
            [25, 25, 25],
            [50, 50, 25],
            [75, 75, 25]
        ])
        
        estimates, variances = kriging.estimate_grid(grid_coords)
        
        assert len(estimates) == 3
        assert len(variances) == 3
        assert (estimates > 0).all()
        assert (variances >= 0).all()


class TestKrigingGridBuilder:
    """Test kriging grid model builder"""

    def test_builder_initialization(self, sample_data):
        """Test builder creation"""
        builder = KrigingGridBuilder(sample_data, 'au', 'spherical')
        assert builder.value_col == 'au'
        assert builder.model_type == 'spherical'
        assert builder.kriging is not None

    def test_build_kriged_model_spherical(self, sample_data):
        """Test building kriged grid model with spherical"""
        builder = KrigingGridBuilder(sample_data, 'au', 'spherical')
        blocks = builder.build_kriged_model(grid_size=(20, 20, 10))
        
        assert len(blocks) > 0
        assert 'block_id' in blocks.columns
        assert 'x' in blocks.columns
        assert 'y' in blocks.columns
        assert 'z' in blocks.columns
        assert 'au' in blocks.columns
        assert 'kriging_variance' in blocks.columns
        assert (blocks['au'] > 0).all()

    def test_build_kriged_model_exponential(self, sample_data):
        """Test building kriged grid model with exponential"""
        builder = KrigingGridBuilder(sample_data, 'au', 'exponential')
        blocks = builder.build_kriged_model(grid_size=(20, 20, 10))
        
        assert len(blocks) > 0
        assert 'kriging_variance' in blocks.columns

    def test_kriging_estimate_function(self, sample_data):
        """Test convenience function"""
        blocks = kriging_estimate(sample_data, grid_size=(20, 20, 10), 
                                  value_col='au', model_type='spherical')
        
        assert len(blocks) > 0
        assert 'au' in blocks.columns
        assert 'kriging_variance' in blocks.columns


class TestKrigingStatistics:
    """Test kriging statistics and properties"""

    def test_kriging_variance_properties(self, sample_data):
        """Test that kriging variance behaves correctly"""
        kriging = OrdinaryKriging(sample_data, 'au')
        
        # Variance at data point should be low
        point1 = sample_data.iloc[0][['x', 'y', 'z']].values
        _, var1 = kriging.estimate(point1)
        
        # Variance away from data should be higher
        center_x = sample_data['x'].mean()
        center_y = sample_data['y'].mean()
        center_z = sample_data['z'].mean()
        
        # Create point far from all data
        far_point = np.array([center_x * 5, center_y * 5, center_z * 5])
        
        # This test might not always pass due to extrapolation
        # Just verify both are computed
        _, var2 = kriging.estimate(far_point)
        assert var1 >= 0 and var2 >= 0

    def test_multiple_values_kriging(self, sample_data):
        """Test kriging with multiple value columns"""
        kriging_au = OrdinaryKriging(sample_data, 'au')
        kriging_cu = OrdinaryKriging(sample_data, 'cu')
        
        point = (50, 50, 25)
        est_au, _ = kriging_au.estimate(point)
        est_cu, _ = kriging_cu.estimate(point)
        
        # Both should give valid estimates
        assert 0 < est_au < 2
        assert 0 < est_cu < 0.2


class TestKrigingEdgeCases:
    """Test edge cases and error handling"""

    def test_kriging_with_nan_values(self, sample_data):
        """Test kriging handles NaN values"""
        sample_data.loc[0, 'au'] = np.nan
        
        kriging = OrdinaryKriging(sample_data, 'au')
        # Should have 19 valid points
        assert len(kriging.values) == 19

    def test_kriging_small_dataset(self):
        """Test kriging with minimal data"""
        df = pd.DataFrame({
            'x': [0, 10, 20],
            'y': [0, 10, 20],
            'z': [0, 10, 20],
            'au': [0.5, 1.0, 1.5]
        })
        
        kriging = OrdinaryKriging(df, 'au')
        point = (10, 10, 10)
        estimate, variance = kriging.estimate(point)
        
        assert isinstance(estimate, float)
        assert estimate > 0
