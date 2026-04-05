"""Tests for proyectovulcano.block_model module."""

import pandas as pd
import numpy as np
import pytest

from proyectovulcano.block_model import build_regular_block_model


@pytest.fixture
def sample_composites():
    """Create sample composites."""
    return pd.DataFrame({
        "hole_id": ["AH1"] * 4 + ["AH2"] * 4,
        "x": [100.0] * 4 + [150.0] * 4,
        "y": [200.0] * 4 + [250.0] * 4,
        "z": [0.0, -10.0, -20.0, -30.0] * 2,
        "au": [0.5, 0.6, 0.4, 0.3, 0.4, 0.7, 0.5, 0.6],
        "comp_from": [0, 10, 20, 30] * 2,
        "comp_to": [10, 20, 30, 40] * 2,
    })


def test_build_regular_block_model_basic(sample_composites):
    """Test basic block model building."""
    blocks = build_regular_block_model(
        sample_composites,
        value_col="au",
        cell_size=(20.0, 20.0, 10.0),
        padding=(0.0, 0.0, 0.0),
        power=2.0,
        search_radius=30.0,
        max_samples=12,
    )
    
    assert not blocks.empty
    assert "au" in blocks.columns
    assert "x" in blocks.columns
    assert "y" in blocks.columns
    assert "z" in blocks.columns
    assert "n_used" in blocks.columns


def test_build_block_model_with_padding(sample_composites):
    """Test block model with padding."""
    blocks = build_regular_block_model(
        sample_composites,
        value_col="au",
        cell_size=(10.0, 10.0, 5.0),
        padding=(10.0, 10.0, 5.0),
    )
    
    assert not blocks.empty
    # Blocks should extend beyond original data due to padding
    assert blocks["x"].min() < sample_composites["x"].min()
    assert blocks["x"].max() > sample_composites["x"].max()


def test_build_block_model_missing_value_col():
    """Test error with missing value column."""
    df = pd.DataFrame({
        "x": [100.0],
        "y": [200.0],
        "z": [0.0],
    })
    
    with pytest.raises(ValueError, match="Column not found for estimation"):
        build_regular_block_model(df, value_col="missing_col")


def test_build_block_model_invalid_cell_size(sample_composites):
    """Test error with invalid cell size."""
    with pytest.raises(ValueError, match="cell_size values must be > 0"):
        build_regular_block_model(
            sample_composites,
            value_col="au",
            cell_size=(0.0, 10.0, 5.0),
        )


def test_build_block_model_empty_after_cleanup():
    """Test error when all data is NaN after cleanup."""
    df = pd.DataFrame({
        "x": [100.0, 150.0],
        "y": [200.0, 250.0],
        "z": [0.0, -10.0],
        "au": [np.nan, np.nan],
    })
    
    with pytest.raises(ValueError, match="No valid composites available"):
        build_regular_block_model(df, value_col="au")


def test_build_block_model_idw_parameters(sample_composites):
    """Test different IDW parameters."""
    blocks1 = build_regular_block_model(
        sample_composites,
        value_col="au",
        power=2.0,
        search_radius=20.0,
    )
    
    blocks2 = build_regular_block_model(
        sample_composites,
        value_col="au",
        power=3.0,
        search_radius=30.0,
    )
    
    # Should produce different results due to different parameters
    assert not blocks1.empty and not blocks2.empty
    assert len(blocks1) == len(blocks2)
