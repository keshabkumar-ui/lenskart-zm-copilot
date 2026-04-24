import os
import pandas as pd
from pdf_generator import create_pdf_report
from engine import analyze_stores, load_data

def test_pdf_stability():
    print("[1/2] Loading real data for PDF test...")
    df = load_data("stores_data.parquet")
    decisions = analyze_stores(df)
    
    # Pick a store
    d = decisions[0]
    
    print(f"[2/2] Generating test report for Store {d['store_id']}...")
    
    try:
        # Correctly pass all 9 arguments
        pdf_bytes = create_pdf_report(
            d["store_id"],
            d["city"],
            d["metrics"],
            d["health_score"],
            d["health_label"],
            d["signals"],
            d["trends"],
            "MOCK AI REPORT: Optimization required for conversion recovery.",
            d.get("benchmarks", {})
        )
        
        if pdf_bytes:
            print("SUCCESS: PDF generated in memory.")
            # Verify file writing
            with open("test_final.pdf", "wb") as f:
                f.write(pdf_bytes)
            print("SUCCESS: PDF saved to disk (test_final.pdf).")
            os.remove("test_final.pdf")
        else:
            print("FAILED: PDF bytes empty.")
            
    except Exception as e:
        print(f"FAILED with error: {e}")

if __name__ == "__main__":
    test_pdf_stability()
