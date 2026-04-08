"""
scripts/run_pipeline.py
=======================
Fetch → Merge → Clean → Save

Run this once to build the cleaned dataset used by the Streamlit app
and any further analysis.

Usage:
    python scripts/run_pipeline.py

Outputs (written to data/):
    usgs_raw.csv      — raw USGS fetch
    ncei_raw.csv      — raw NCEI fetch
    merged.csv        — after approximate match
    cleaned.csv       — after cleaning (use this for analysis)
"""

import os
import sys

# Allow running from the repo root without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from earthquake_analysis.fetch import fetch_ncei, fetch_usgs
from earthquake_analysis.merge import merge_usgs_ncei
from earthquake_analysis.clean import clean_merged

DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
START_DATE = "2000-01-01"
END_DATE   = "2024-12-31"
MIN_YEAR   = 2000
MAX_YEAR   = 2024


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # ── 1. Fetch ──────────────────────────────────────────────────────────────
    print("=== Fetching NCEI data ===")
    df_ncei = fetch_ncei(min_year=MIN_YEAR, max_year=MAX_YEAR)
    ncei_path = os.path.join(DATA_DIR, "ncei_raw.csv")
    df_ncei.to_csv(ncei_path, index=False)
    print(f"Saved {len(df_ncei)} NCEI records → {ncei_path}\n")

    print("=== Fetching USGS data ===")
    df_usgs = fetch_usgs(start_date=START_DATE, end_date=END_DATE)
    usgs_path = os.path.join(DATA_DIR, "usgs_raw.csv")
    df_usgs.to_csv(usgs_path, index=False)
    print(f"Saved {len(df_usgs)} USGS records → {usgs_path}\n")

    # ── 2. Merge ──────────────────────────────────────────────────────────────
    print("=== Merging USGS + NCEI ===")
    # Ensure time columns are proper Timestamps before merging
    df_usgs["time"] = pd.to_datetime(df_usgs["time"], utc=True, errors="coerce")
    df_ncei["time"] = pd.to_datetime(df_ncei["time"], utc=True, errors="coerce")

    merged = merge_usgs_ncei(df_usgs, df_ncei)
    merged_path = os.path.join(DATA_DIR, "merged.csv")
    merged.to_csv(merged_path, index=False)
    print(f"Saved {len(merged)} merged records → {merged_path}\n")

    # ── 3. Clean ──────────────────────────────────────────────────────────────
    print("=== Cleaning merged data ===")
    cleaned = clean_merged(merged)
    cleaned_path = os.path.join(DATA_DIR, "cleaned.csv")
    cleaned.to_csv(cleaned_path, index=False)
    print(f"Saved {len(cleaned)} cleaned records → {cleaned_path}\n")

    print("Pipeline complete. Use data/cleaned.csv for analysis.")


if __name__ == "__main__":
    main()
