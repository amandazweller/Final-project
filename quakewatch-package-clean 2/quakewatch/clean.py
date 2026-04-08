# quakewatch/clean.py
#
# This module cleans the MERGED earthquake DataFrame (after fetch + merge).
#
# Cleaning after merging means we only need one function instead of two,
# and we clean the actual columns we'll use for analysis — not just each
# source in isolation.

import pandas as pd


def clean_merged(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the merged USGS + NCEI DataFrame (output of merge_datasets).

    Call this AFTER fetch_usgs, fetch_ncei, and merge_datasets have run.

    Steps
    -----
    1. Drop rows missing latitude, longitude, or time  (can't use without these).
    2. Drop rows missing magnitude                      (central to every analysis).
    3. Clip magnitude to [0, 10]                        (physically valid range).
    4. Remove rows with negative depth                  (data entry errors).
    5. Convert all numeric columns to proper float type.
    6. Fill missing impact values with 0
       (no reported deaths in NCEI likely means 0, not unknown).
    7. Remove rows with impossible coordinates          (lat outside +-90, lon outside +-180).
    8. Reset the index so row numbers run 0, 1, 2, ...

    Parameters
    ----------
    df : pd.DataFrame
        Merged DataFrame from merge_datasets().

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame ready for analysis.

    Example
    -------
    >>> from quakewatch.fetch import fetch_usgs, fetch_ncei
    >>> from quakewatch.merge import merge_datasets
    >>> from quakewatch.clean import clean_merged
    >>>
    >>> usgs = fetch_usgs("2010-01-01", "2023-12-31", min_magnitude=4.0)
    >>> ncei = fetch_ncei()
    >>> merged = merge_datasets(usgs, ncei)
    >>> df = clean_merged(merged)
    """
    print(f"Cleaning merged data: starting with {len(df):,} rows")

    df = df.copy()  # don't modify the original DataFrame

    # ------------------------------------------------------------------
    # Step 1 — drop rows without location or time
    # ------------------------------------------------------------------
    df = df.dropna(subset=["latitude", "longitude", "time"])

    # ------------------------------------------------------------------
    # Step 2 — drop rows without magnitude
    # ------------------------------------------------------------------
    df = df.dropna(subset=["magnitude"])

    # ------------------------------------------------------------------
    # Step 3 — magnitude must be between 0 and 10
    # pd.to_numeric(..., errors="coerce") turns bad values into NaN
    # clip() replaces anything above 10 with 10 (doesn't delete the row)
    # ------------------------------------------------------------------
    df["magnitude"] = pd.to_numeric(df["magnitude"], errors="coerce")
    df = df[df["magnitude"] >= 0]           # remove negatives (data errors)
    df["magnitude"] = df["magnitude"].clip(upper=10.0)

    # ------------------------------------------------------------------
    # Step 4 — depth must be non-negative (km below the surface)
    # We allow NaN depth (some records don't have it) but not negatives
    # ------------------------------------------------------------------
    df["depth"] = pd.to_numeric(df["depth"], errors="coerce")
    df = df[df["depth"].isna() | (df["depth"] >= 0)]

    # ------------------------------------------------------------------
    # Step 5 — convert numeric columns to proper float type
    # ------------------------------------------------------------------
    numeric_cols = ["sig", "mmi", "felt", "ncei_magnitude"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ------------------------------------------------------------------
    # Step 6 — fill missing impact values with 0
    # These columns come from NCEI via the merge. Rows that didn't match
    # any NCEI record have NaN here, which we treat as 0 impact.
    # ------------------------------------------------------------------
    impact_cols = ["deaths", "injuries", "damage_millions_dollars", "houses_destroyed"]
    for col in impact_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ------------------------------------------------------------------
    # Step 7 — remove rows with impossible coordinates
    # ------------------------------------------------------------------
    df = df[df["latitude"].between(-90, 90)]
    df = df[df["longitude"].between(-180, 180)]

    # ------------------------------------------------------------------
    # Step 8 — reset the index
    # After dropping rows, row numbers have gaps (0, 1, 4, 7...).
    # This renumbers them cleanly from 0.
    # ------------------------------------------------------------------
    df = df.reset_index(drop=True)

    print(f"Cleaning merged data: finished with {len(df):,} rows")
    return df
