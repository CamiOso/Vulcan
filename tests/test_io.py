"""Tests for proyectovulcano.io module."""

import pandas as pd
import pytest
from pathlib import Path
import tempfile

from proyectovulcano.io import (
    load_drillholes_csv,
    filter_by_domain,
    list_numeric_columns,
    list_categorical_columns,
    export_dataframe_csv,
    export_dataframe_json,
)


@pytest.fixture
def sample_drillholes_df():
    """Create sample drillholes dataframe."""
    return pd.DataFrame({
        "hole_id": ["AH1", "AH1", "AH1", "AH2", "AH2"],
        "x": [100.0, 100.0, 100.0, 200.0, 200.0],
        "y": [200.0, 200.0, 200.0, 300.0, 300.0],
        "z": [0.0, -10.0, -20.0, 0.0, -10.0],
        "au": [0.5, 0.7, 0.3, 0.4, 0.6],
        "lith": ["granite", "granite", "schist", "granite", "schist"],
    })


def test_filter_by_domain(sample_drillholes_df):
    """Test domain filtering."""
    df = sample_drillholes_df
    
    # Filter by single domain value
    result = filter_by_domain(df, domain_col="lith", domain_values=["granite"])
    assert len(result) == 3
    assert all(result["lith"] == "granite")
    
    # Filter by multiple values
    result = filter_by_domain(df, domain_col="lith", domain_values=["granite", "schist"])
    assert len(result) == 5
    
    # Filter with no column
    result = filter_by_domain(df)
    assert len(result) == 5


def test_filter_by_domain_missing_column(sample_drillholes_df):
    """Test error when domain column missing."""
    with pytest.raises(ValueError, match="Domain column not found"):
        filter_by_domain(sample_drillholes_df, domain_col="missing_col")


def test_list_numeric_columns(sample_drillholes_df):
    """Test numeric column listing."""
    numeric = list_numeric_columns(sample_drillholes_df)
    assert set(numeric) == {"x", "y", "z", "au"}


def test_list_categorical_columns(sample_drillholes_df):
    """Test categorical column listing."""
    categorical = list_categorical_columns(sample_drillholes_df)
    assert set(categorical) == {"hole_id", "lith"}


def test_export_csv(sample_drillholes_df):
    """Test CSV export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.csv"
        export_dataframe_csv(sample_drillholes_df, path)
        assert path.exists()
        
        # Verify content
        loaded = pd.read_csv(path)
        assert len(loaded) == len(sample_drillholes_df)
        assert list(loaded.columns) == list(sample_drillholes_df.columns)


def test_export_json(sample_drillholes_df):
    """Test JSON export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.json"
        export_dataframe_json(sample_drillholes_df, path)
        assert path.exists()
        
        # Verify content
        loaded = pd.read_json(path)
        assert len(loaded) == len(sample_drillholes_df)
