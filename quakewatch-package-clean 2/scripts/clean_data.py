#!/usr/bin/env python3
# scripts/clean_data.py
#
# Standalone script to:
#   1. Fetch raw data from USGS and NCEI
#   2. Merge the two datasets
#   3. Clean the merged result
#   4. Save to data/merged_earthquakes.csv
#
# Run from the project root:
#   python scripts/clean_data.py
#
# Adjust START_DATE, END_DATE, and MIN_MAGNITUDE below as needed.

import os
import sys

# Add the project root to Python's path so we can import 'quakewatch'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quakewatch.fetch import fetch_usgs, fetch_ncei
from quakewatch.merge import merge_datasets
from quakewatch.clean import clean_merged

# ── Configuration ─────────────────────────────────────────────────────────────
START_DATE    = "2000-01-01"
END_DATE      = "2005-12-31"
MIN_MAGNITUDE = 0

OUTPUT_DIR  = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "merged_earthquakes.csv")
# ──────────────────────────────────────────────────────────────────────────────


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("QuakeWatch — Data Pipeline")
    print("Order: fetch → merge → clean")
    print("=" * 60)

    # Step 1: Fetch raw data
    print("\n[1/3] Fetching USGS data ...")
    usgs_raw = fetch_usgs(
        start_date=START_DATE,
        end_date=END_DATE,
        min_magnitude=MIN_MAGNITUDE,
    )

    print("\n[2/3] Fetching NCEI data ...")
    ncei_raw = fetch_ncei(2000, 2005, min_magnitude=MIN_MAGNITUDE)  # NCEI API uses years, not dates
    rename_map = {
        "eqMagnitude":           "magnitude",
        "deaths":                "deaths",
        "injuries":              "injuries",
        "damageMillionsDollars": "damage_millions_dollars",
        "housesDestroyed":       "houses_destroyed",
        "year":                  "year",
        "month":                 "month",
        "day":                   "day",
        "locationName":          "location_name",
        "country":               "country",
        "latitude":              "latitude",
        "longitude":             "longitude",
    }
    existing = {k: v for k, v in rename_map.items() if k in ncei_raw.columns}
    ncei_raw = ncei_raw.rename(columns=existing)

    # Step 2: Merge first
    print("\n[3/4] Merging datasets ...")
    merged = merge_datasets(usgs_raw, ncei_raw)

    # Step 3: Clean the merged result
    print("\n[4/4] Cleaning merged data ...")
    df = clean_merged(merged)

    # Step 4: Save
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Saved {len(df):,} rows to:\n   {OUTPUT_FILE}")
    print("\nColumn overview:")
    print(df.dtypes.to_string())


if __name__ == "__main__":
    main()
