"""
merge.py — Approximate-match NCEI significant earthquakes onto USGS events.

Strategy (from the exploration notebook):
  1. Time window  : ±3 days
  2. Spatial box  : ±1° lat/lon (~111 km)
  3. Tiebreaker   : closest magnitude match

USGS is the source of truth for physics (magnitude, depth, location).
NCEI enriches matched rows with human-impact data (deaths, damage, etc.).
"""

import numpy as np
import pandas as pd


def merge_usgs_ncei(
    df_usgs: pd.DataFrame,
    df_ncei: pd.DataFrame,
    time_tolerance_days: int = 3,
    coord_tolerance_deg: float = 1.0,
) -> pd.DataFrame:
    """
    Left-join NCEI significant earthquakes onto USGS events.

    For each NCEI record, finds the best-matching USGS record by:
      - time within ±time_tolerance_days
      - lat/lon within ±coord_tolerance_deg
      - closest eqMagnitude as tiebreaker

    All NCEI columns are prefixed with 'ncei_'.
    All USGS columns are prefixed with 'usgs_'.

    Returns a DataFrame of matched rows only.
    Unmatched NCEI rows (no USGS event found) are silently dropped.
    """
    time_delta = pd.Timedelta(days=time_tolerance_days)
    matched = []

    for _, ncei_row in df_ncei.iterrows():
        # Skip records with no time or location — can't match without them
        if pd.isna(ncei_row["time"]) or pd.isna(ncei_row.get("latitude")):
            continue

        # 1. Filter USGS to the time window
        time_mask = (
            (df_usgs["time"] >= ncei_row["time"] - time_delta) &
            (df_usgs["time"] <= ncei_row["time"] + time_delta)
        )
        candidates = df_usgs[time_mask].copy()
        if candidates.empty:
            continue

        # 2. Filter by spatial proximity
        candidates = candidates[
            (np.abs(candidates["latitude"]  - ncei_row["latitude"])  <= coord_tolerance_deg) &
            (np.abs(candidates["longitude"] - ncei_row["longitude"]) <= coord_tolerance_deg)
        ]
        if candidates.empty:
            continue

        # 3. Pick the candidate whose magnitude is closest to the NCEI magnitude
        ncei_mag = ncei_row.get("eqMagnitude")
        if pd.notna(ncei_mag):
            best_idx = (candidates["magnitude"] - float(ncei_mag)).abs().idxmin()
        else:
            best_idx = candidates.index[0]

        usgs_match = candidates.loc[best_idx]
        row = {
            **{f"ncei_{k}": v for k, v in ncei_row.items()},
            **{f"usgs_{k}": v for k, v in usgs_match.items()},
        }
        matched.append(row)

    result = pd.DataFrame(matched)
    match_rate = len(result) / len(df_ncei) if len(df_ncei) > 0 else 0
    print(f"Merged: {len(result)} / {len(df_ncei)} NCEI records matched ({match_rate:.1%})")
    return result
