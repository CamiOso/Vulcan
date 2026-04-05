"""Tests for proyectovulcano.stats module."""

import pandas as pd
import numpy as np
import pytest

from proyectovulcano.stats import (
    compare_composites_vs_blocks,
    format_stats_report,
    get_drillhole_statistics,
    detect_outliers_iqr,
    get_data_quality_report,
)


@pytest.fixture
def sample_data():
    """Create sample data for stats testing."""
    composites = pd.DataFrame({
        "hole_id": ["AH1", "AH1", "AH2", "AH2"],
        "au": [0.5, 0.6, 0.4, 0.7],
        "x": [100, 100, 200, 200],
        "y": [200, 200, 300, 300],
        "z": [0, -20, 0, -20],
    })
    
    blocks = pd.DataFrame({
        "x": [100, 150, 200],
        "y": [200, 250, 300],
        "z": [0, -10, -20],
        "au": [0.55, 0.65, 0.55],
    })
    
    return composites, blocks


def test_compare_composites_vs_blocks(sample_data):
    """Test comparison statistics."""
    composites, blocks = sample_data
    
    report = compare_composites_vs_blocks(composites, blocks, value_col="au")
    
    assert "composites" in report
    assert "blocks" in report
    assert report["composites"]["count"] == 4.0
    assert report["blocks"]["count"] == 3.0


def test_format_stats_report(sample_data):
    """Test report formatting."""
    composites, blocks = sample_data
    
    report = compare_composites_vs_blocks(composites, blocks, value_col="au")
    text = format_stats_report(report, value_col="au")
    
    assert "Validation Report" in text
    assert "composites" in text
    assert "blocks" in text
    assert "mean" in text


def test_get_drillhole_statistics(sample_data):
    """Test drillhole-level statistics."""
    composites, _ = sample_data
    
    stats = get_drillhole_statistics(composites)
    
    assert "AH1" in stats
    assert "AH2" in stats
    assert "au" in stats["AH1"]
    assert "hole_length" in stats["AH1"]


def test_detect_outliers_iqr():
    """Test outlier detection."""
    series = pd.Series([1, 2, 3, 4, 5, 100])  # 100 is outlier
    
    outliers = detect_outliers_iqr(series, k=1.5)
    
    assert outliers.sum() > 0
    assert outliers.iloc[-1] == True  # Last value (100) should be outlier


def test_get_data_quality_report(sample_data):
    """Test data quality report."""
    composites, _ = sample_data
    
    report = get_data_quality_report(composites)
    
    assert report["total_rows"] == 4
    assert report["total_columns"] == 5
    assert "numeric_columns" in report
    assert "categorical_columns" in report
    assert len(report["numeric_columns"]) > 0
