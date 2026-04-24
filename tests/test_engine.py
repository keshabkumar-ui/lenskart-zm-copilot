import pytest
import pandas as pd
import numpy as np
import os
import sqlite3
from engine import compute_kpis, compute_trends, detect_signals, analyze_stores, THRESHOLDS
from learning_engine import init_db, save_feedback, get_historical_patterns, DB_PATH

def test_kpi_calculation():
    """Verify that core KPIs are calculated correctly from raw metrics."""
    data = {
        "store_id": ["S1"],
        "date": [pd.Timestamp("2024-01-01")],
        "footfall": [100],
        "transactions": [10],
        "revenue": [1000],
        "staff_count": [2]
    }
    df = pd.DataFrame(data)
    processed = compute_kpis(df)
    
    assert processed.iloc[0]["conversion_rate"] == 10.0
    assert processed.iloc[0]["aov"] == 100.0
    assert processed.iloc[0]["staff_efficiency"] == 5.0

def test_revenue_bridge_decomposition():
    """Verify the explicit revenue decomposition in analyze_stores."""
    data = {
        "store_id": ["S1", "S1"],
        "city": ["Bangalore", "Bangalore"],
        "date": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")],
        "footfall": [100, 150],      # Footfall increases
        "transactions": [10, 10],    # Transactions stay same
        "revenue": [1000, 1000],     # Revenue stays same
        "staff_count": [2, 2]
    }
    df = pd.DataFrame(data)
    results = analyze_stores(df)
    
    store_res = results[0]
    assert "decomposition" in store_res
    decomp = store_res["decomposition"]
    
    # Footfall increased, so footfall_effect should be positive
    assert decomp["footfall_effect"] > 0
    # Conversion rate dropped (10/100 -> 10/150), so conversion_effect should be negative
    assert decomp["conversion_effect"] < 0
    # Total delta is 0
    assert decomp["total_delta"] == 0

def test_signal_vectorizer():
    """Verify the AI-native signal vectorizer returns raw anomalies."""
    T = THRESHOLDS
    row = {
        "store_id": "S1",
        "footfall": T["bottleneck_footfall"] + 100,
        "conversion_rate": T["conversion"]["warning"] - 2,
        "staff_efficiency": T["staff_eff"]["warning"] - 1,
        "revenue": 1000,
        "aov": 100,
        "staff_count": 2
    }
    trends = {"S1": {"trend_label": "STABLE"}}
    vector = detect_signals(row, trends, None)
    
    tags = [s["tag"] for s in vector]
    assert "HIGH_FOOTFALL" in tags
    assert "CONVERSION_LOW" in tags
    assert "STAFF_EFFICIENCY_LOW" in tags

def test_learning_engine_feedback_loop():
    """Verify that feedback is persisted and affects historical patterns."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    init_db()
    issue = "TEST_ISSUE"
    action = "TEST_ACTION"
    
    # Save positive feedback
    save_feedback("T1", issue, action, "positive", {"m": 1})
    patterns = get_historical_patterns(issue)
    
    assert patterns["similar_cases"] == 1
    assert patterns["success_rate"] == 1.0
    
    # Save negative feedback
    save_feedback("T2", issue, action, "negative", {"m": 1})
    patterns = get_historical_patterns(issue)
    
    assert patterns["similar_cases"] == 2
    assert patterns["success_rate"] == 0.5

def test_adaptive_confidence_logic():
    """Verify that engine utilizes patterns for its logic (indirectly through confidence)."""
    # This test ensures the learning engine functions are integrated into the main flow
    data = {
        "store_id": ["S1", "S1"],
        "city": ["Bangalore", "Bangalore"],
        "date": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")],
        "footfall": [100, 110],
        "transactions": [10, 11],
        "revenue": [1000, 1100],
        "staff_count": [2, 2]
    }
    df = pd.DataFrame(data)
    results = analyze_stores(df)
    
    # If no historical data, similar_cases in patterns (via generate_report prompt construction) 
    # would be handled, but here we just check if analyze_stores runs without error 
    # and includes the new data model keys.
    assert len(results) > 0
    assert "decomposition" in results[0]
