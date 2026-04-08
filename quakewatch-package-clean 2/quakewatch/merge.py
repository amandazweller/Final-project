# quakewatch/merge.py
#
# Merges the USGS and NCEI datasets.
#
# Strategy
# --------
# USGS has ~millions of earthquakes; NCEI has ~5,700 significant ones.
# We try to match each NCEI earthquake to the closest USGS earthquake using:
#   - Time window: within +-3 days
#   - Location window: within +-1 degree of latitude AND longitude
#   - Among candidates: pick the one with the closest magnitude
#
# USGS is the "left" (primary) dataset.
# NCEI columns (deaths, damage, etc.) are added to matching USGS rows.
#
# NOTE: Run clean_merged() from clean.py AFTER this function, not before.

import pandas as pd
import numpy as np
import time


def merge_datasets(
    usgs: pd.DataFrame,
    ncei: pd.DataFrame,
    time_tolerance_days: float = 3.0,
    location_tolerance_deg: float = 1.0,
) -> pd.DataFrame:
    """
    Merge USGS and NCEI earthquake DataFrames.

    For each NCEI earthquake, find the best-matching USGS earthquake
    within the given time and location tolerances. NCEI impact columns
    are added to the matched USGS row. USGS rows with no match keep
    NaN for the impact columns.

    Run clean_merged() on the result of this function to clean the
    combined dataset.

    Parameters
    ----------
    usgs : pd.DataFrame
        Raw USGS DataFrame from fetch_usgs().
    ncei : pd.DataFrame
        Raw NCEI DataFrame from fetch_ncei().
    time_tolerance_days : float
        Max difference in days between USGS and NCEI event times.
    location_tolerance_deg : float
        Max difference in degrees (lat or lon) between events.

    Returns
    -------
    pd.DataFrame
        USGS DataFrame with added columns from NCEI:
        deaths, injuries, damage_millions_dollars, houses_destroyed,
        ncei_magnitude (for reference), ncei_location.
    """

    print("Merging USGS and NCEI datasets ...")

    usgs = usgs.copy()
    ncei = ncei.copy()

    # -----------------------------------------------------------------------
    # Prepare NCEI: build a 'date' column from year/month/day columns
    # and make sure coordinates are numeric.
    # (We do the minimum prep needed here to perform the join.
    #  Full cleaning happens in clean_merged() afterward.)
    # -----------------------------------------------------------------------
    ncei["year"]  = pd.to_numeric(ncei.get("year"),  errors="coerce")
    ncei["month"] = pd.to_numeric(ncei.get("month"), errors="coerce").fillna(1).clip(1, 12).astype(int)
    ncei["day"]   = pd.to_numeric(ncei.get("day"),   errors="coerce").fillna(1).clip(1, 28).astype(int)

    ncei["date"] = pd.to_datetime(
        ncei[["year", "month", "day"]],
        errors="coerce",
        utc=True,
    )

    ncei["latitude"]  = pd.to_numeric(ncei.get("latitude"),  errors="coerce")
    ncei["longitude"] = pd.to_numeric(ncei.get("longitude"), errors="coerce")

    # Drop NCEI rows we can't use for matching (no date or no location)
    ncei = ncei.dropna(subset=["date", "latitude", "longitude"])

    # -----------------------------------------------------------------------
    # Prepare USGS: make sure time is a proper datetime
    # -----------------------------------------------------------------------
    usgs["time"] = pd.to_datetime(usgs["time"], utc=True, errors="coerce")

    # -----------------------------------------------------------------------
    # Initialise impact columns in USGS with NaN
    # -----------------------------------------------------------------------
    # impact_cols = ["deaths", "injuries", "damage_millions_dollars", "houses_destroyed"]
    # impact_cols = [c for c in impact_cols if c in ncei.columns]

    # for col in impact_cols:
    #     usgs[col] = np.nan
    # usgs["ncei_magnitude"] = np.nan
    # usgs["ncei_location"]  = np.nan

    # time_tol = pd.Timedelta(days=time_tolerance_days)
    # matched_count = 0

    # -----------------------------------------------------------------------
    # For each NCEI row, find the best USGS match
    # -----------------------------------------------------------------------
    
    def merge_usgs_ncei(df_usgs, df_ncei, time_tolerance_days=3, coord_tolerance_deg=1.0):
        """
        Left-join NCEI significant earthquakes onto USGS events.
        For each NCEI record, find the best-matching USGS record by:
        - time within ±time_tolerance_days
        - lat/lon within ±coord_tolerance_deg
        - closest eqMagnitude as tiebreaker
        """
        time_delta = pd.Timedelta(days=time_tolerance_days)
        matched = []

        for _, ncei_row in df_ncei.iterrows():
            # Skip rows with no time or location
            if pd.isna(ncei_row["time"]) or pd.isna(ncei_row["latitude"]):
                continue

            # Filter USGS to time window
            time_mask = (
                (df_usgs["time"] >= ncei_row["time"] - time_delta) &
                (df_usgs["time"] <= ncei_row["time"] + time_delta)
            )
            candidates = df_usgs[time_mask].copy()
            if candidates.empty:
                continue

            # Filter by spatial proximity
            candidates = candidates[
                (np.abs(candidates["latitude"]  - ncei_row["latitude"])  <= coord_tolerance_deg) &
                (np.abs(candidates["longitude"] - ncei_row["longitude"]) <= coord_tolerance_deg)
            ]
            if candidates.empty:
                continue

            # Pick closest by magnitude — NOTE: NCEI column is eqMagnitude, not magnitude
            if pd.notna(ncei_row.get("eqMagnitude")):
                best_idx = (candidates["magnitude"] - ncei_row["magnitude"]).abs().idxmin()
            else:
                best_idx = candidates.index[0]

            usgs_match = candidates.loc[best_idx]
            row = {
                **{f"ncei_{k}": v for k, v in ncei_row.items()},
                **{f"usgs_{k}": v for k, v in usgs_match.items()},
            }
            matched.append(row)

        result = pd.DataFrame(matched)
        print(f"Matched {len(result)} / {len(df_ncei)} NCEI records to a USGS event ({len(result)/len(df_ncei):.1%})")
        return result


    merged = merge_usgs_ncei(usgs, ncei)
    return merged
