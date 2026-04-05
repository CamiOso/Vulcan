#!/usr/bin/env python3
"""
v0.6.0 Integration Test - ML GUI Functionality
Tests ML parameter passing and block model building with selected algorithms
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.proyectovulcano.io import load_drillholes_csv
from src.proyectovulcano.compositing import composite_drillholes
from src.proyectovulcano.block_model import build_regular_block_model

def test_ml_gui_integration():
    """Test ML integration with GUI parameter passing"""
    
    # Load example data
    data_path = Path("data/example_drillholes.csv")
    if not data_path.exists():
        print("❌ Test data not found")
        return False
    
    drillholes = load_drillholes_csv(data_path)
    print(f"✓ Loaded {len(drillholes)} drillhole samples")
    
    # Create composites
    composites = composite_drillholes(drillholes, value_col="au", composite_length=10.0)
    print(f"✓ Created {len(composites)} composites")
    
    # Test parameters - simulating GUI inputs
    grid_size = (10.0, 10.0, 5.0)
    value_col = "au"
    ml_params = {
        "normalize": True,
        "cv_folds": 5,
        "n_estimators": 50,
        "max_depth": 8,
        "learning_rate": 0.1
    }
    
    # Test each estimation method via GUI-style call
    methods = ["idw", "linear", "rf", "gb"]
    results = {}
    
    for method in methods:
        try:
            print(f"\n🔄 Testing method: {method.upper()}")
            
            kwargs = {
                "grid_size": grid_size,
                "value_col": value_col,
                "power": 2.0,
                "search_radius": 25.0,
                "max_samples": 12,
                "estimation_method": method
            }
            
            # Add ML params for ML methods
            if method in ["linear", "rf", "gb"]:
                kwargs["ml_params"] = ml_params
            
            # This simulates GUI call
            blocks = build_regular_block_model(composites, **kwargs)
            
            mean_val = blocks[value_col].mean()
            std_val = blocks[value_col].std()
            count = len(blocks)
            
            results[method] = {
                "mean": round(mean_val, 4),
                "std": round(std_val, 4),
                "count": count,
                "status": "✓"
            }
            
            print(f"  ✓ {method.upper()}: {count} blocks, µ={mean_val:.4f}, σ={std_val:.4f}")
            
        except Exception as e:
            results[method] = {
                "status": "❌",
                "error": str(e)[:100]
            }
            print(f"  ❌ {method.upper()}: {str(e)[:50]}")
    
    # Summary
    print("\n" + "="*60)
    print("INTEGRATION TEST SUMMARY - v0.6.0")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r.get("status") == "✓")
    total = len(results)
    
    print(f"\n✓ Passed: {passed}/{total} methods")
    
    for method, result in results.items():
        status = result.get("status", "?")
        if status == "✓":
            print(f"  {status} {method.upper()}: {result['count']} blocks")
        else:
            print(f"  {status} {method.upper()}: {result.get('error', 'Unknown error')}")
    
    print("\n✓ ML GUI Integration Test Completed")
    print(f"  - Grid size parameter: {grid_size}")
    print(f"  - ML params accepted: normalize, cv_folds, n_estimators, max_depth, learning_rate")
    print(f"  - All estimation methods callable via GUI pattern")
    
    return passed == total

if __name__ == "__main__":
    import sys
    success = test_ml_gui_integration()
    sys.exit(0 if success else 1)
