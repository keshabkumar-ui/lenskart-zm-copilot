import pandas as pd
from engine import load_data, analyze_stores
import os

def test_integration_full_run():
    """Test the full pipeline from loading to complex analysis."""
    print("\n[1/3] Loading data from parquet...")
    if not os.path.exists("stores_data.parquet"):
        print("SKIP: stores_data.parquet missing.")
        return

    df = load_data("stores_data.parquet")
    print(f"Loaded {len(df)} rows.")

    print("[2/3] Running Fleet Analysis...")
    decisions = analyze_stores(df)
    print(f"Analyzed {len(decisions)} stores.")

    print("[3/3] Verifying data consistency...")
    for d in decisions[:5]: # Check first 5
        assert "health_score" in d
        assert "signals" in d
        assert "metrics" in d
        print(f"  - Store {d['store_id']}: {d['health_label']} ({d['health_score']})")

    print("\n✅ INTEGRATION TEST PASSED")

if __name__ == "__main__":
    test_integration_full_run()
