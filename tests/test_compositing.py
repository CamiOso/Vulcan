"""Tests for proyectovulcano.compositing module."""

import pandas as pd
import numpy as np
import pytest

from proyectovulcano.compositing import composite_drillholes


@pytest.fixture
def sample_drillholes_df():
    """Create sample drillholes with depth."""
    return pd.DataFrame({
        "hole_id": ["AH1"] * 10 + ["AH2"] * 10,
        "x": [100.0] * 10 + [200.0] * 10,
        "y": [200.0] * 10 + [300.0] * 10,
        "z": list(range(0, -100, -10)) + list(range(0, -100, -10)),
        "depth": list(range(0, 100, 10)) + list(range(0, 100, 10)),
        "au": [0.5, 0.6, 0.4, 0.7, 0.3, 0.5, 0.4, 0.6, 0.5, 0.3] +
              [0.4, 0.5, 0.6, 0.3, 0.7, 0.4, 0.5, 0.3, 0.6, 0.4],
    })


def test_composite_drillholes_basic(sample_drillholes_df):
    """Test basic compositing with fixed length."""
    composites = composite_drillholes(
        sample_drillholes_df,
        value_col="au",
        composite_length=20.0,
    )
    
    assert not composites.empty
    assert "hole_id" in composites.columns
    assert "au" in composites.columns
    assert "n_samples" in composites.columns
    assert all(composites["hole_id"].isin(["AH1", "AH2"]))


def test_composite_drillholes_length_validation():
    """Test error with invalid composite length."""
    df = pd.DataFrame({
        "hole_id": ["AH1"],
        "x": [100.0],
        "y": [200.0],
        "z": [0.0],
        "au": [0.5],
    })
    
    with pytest.raises(ValueError, match="composite_length must be > 0"):
        composite_drillholes(df, value_col="au", composite_length=-5.0)


def test_composite_drillholes_missing_column():
    """Test error with missing value column."""
    df = pd.DataFrame({
        "hole_id": ["AH1"],
        "x": [100.0],
        "y": [200.0],
        "z": [0.0],
    })
    
    with pytest.raises(ValueError, match="Column not found"):
        composite_drillholes(df, value_col="missing_col", composite_length=10.0)


def test_composite_drillholes_with_nas(sample_drillholes_df):
    """Test compositing handles NAs in value column."""
    df = sample_drillholes_df.copy()
    df.loc[0:2, "au"] = np.nan
    
    composites = composite_drillholes(df, value_col="au", composite_length=20.0)
    assert not composites.empty
    # Should still have composites from non-NA values
    assert len(composites) > 0
