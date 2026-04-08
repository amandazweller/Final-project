"""
clean.py — Clean the merged USGS+NCEI earthquake dataset.

Main entry point:
    clean_merged(df) → cleaned DataFrame

Steps:
  1. Coerce impact and physics columns to numeric.
  2. Drop duplicate USGS events (same usgs_id matched twice).
  3. Remove rows with no usable magnitude.
  4. Add a 'magnitude' convenience column (USGS preferred, NCEI fallback).
  5. Add a 'year' column from usgs_time.
  6. Add a 'depth_category' column (shallow / intermediate / deep).
  7. Add a 'region' column parsed from ncei_locationName.
  8. Drop NCEI columns that duplicate USGS data (time, lat/lon, depth, date parts).
  9. Rename all remaining columns to clean, consistent snake_case names.
"""

import numpy as np
import pandas as pd


# Impact columns that should be numeric
IMPACT_COLS = [
    "ncei_deaths",
    "ncei_injuries",
    "ncei_damageMillionsDollars",
    "ncei_housesDestroyed",
    "ncei_housesDamaged",
]

# USGS physics columns
PHYSICS_COLS = [
    "usgs_magnitude",
    "usgs_depth",
    "usgs_latitude",
    "usgs_longitude",
    "usgs_sig",
    "usgs_mmi",
]

# NCEI columns that duplicate USGS data — dropped after merge
NCEI_DUPLICATE_COLS = [
    "ncei_time",
    "ncei_latitude",
    "ncei_longitude",
    "ncei_year",
    "ncei_month",
    "ncei_day",
    "ncei_hour",
    "ncei_minute",
    "ncei_second",
    "ncei_eqDepth",   # USGS depth is preferred
]

# Final column rename map (applied after duplicates are dropped)
COLUMN_RENAMES = {
    # USGS — fix double-prefix on id, drop prefix on rest
    "usgs_usgs_id":   "usgs_id",
    "usgs_time":      "time",
    "usgs_latitude":  "latitude",
    "usgs_longitude": "longitude",
    "usgs_depth":     "depth",
    "usgs_magnitude": "usgs_magnitude",  # kept distinct; 'magnitude' convenience col also exists
    "usgs_place":     "place",
    "usgs_sig":       "sig",
    "usgs_mmi":       "mmi",
    "usgs_alert":     "alert",
    # NCEI identifier / location
    "ncei_id":            "ncei_id",
    "ncei_locationName":  "location_name",
    "ncei_country":       "country",
    "ncei_regionCode":    "region_code",
    "ncei_area":          "area",
    "ncei_publish":       "published",
    # NCEI magnitude variants
    "ncei_eqMagnitude":   "ncei_magnitude",
    "ncei_eqMagMb":       "mag_body_wave",
    "ncei_eqMagMw":       "mag_moment",
    "ncei_eqMagMs":       "mag_surface_wave",
    "ncei_eqMagMl":       "mag_local",
    "ncei_eqMagUnk":      "mag_unkown",
    # NCEI impact — deaths
    "ncei_deaths":                  "deaths",
    "ncei_deathsAmountOrder":       "deaths_order",
    "ncei_deathsTotal":             "deaths_total",
    "ncei_deathsAmountOrderTotal":  "deaths_order_total",
    # NCEI impact — injuries
    "ncei_injuries":                    "injuries",
    "ncei_injuriesAmountOrder":         "injuries_order",
    "ncei_injuriesTotal":               "injuries_total",
    "ncei_injuriesAmountOrderTotal":    "injuries_order_total",
    # NCEI impact — missing
    "ncei_missing":                   "missing",
    "ncei_missingAmountOrder":        "missing_order",
    "ncei_missingTotal":              "missing_total",
    "ncei_missingAmountOrderTotal":   "missing_order_total",
    # NCEI impact — damage (dollars)
    "ncei_damageMillionsDollars":       "damage_millions",
    "ncei_damageMillionsDollarsTotal":  "damage_millions_total",
    "ncei_damageAmountOrder":           "damage_order",
    "ncei_damageAmountOrderTotal":      "damage_order_total",
    # NCEI impact — houses destroyed
    "ncei_housesDestroyed":                     "houses_destroyed",
    "ncei_housesDestroyedAmountOrder":          "houses_destroyed_order",
    "ncei_housesDestroyedTotal":                "houses_destroyed_total",
    "ncei_housesDestroyedAmountOrderTotal":     "houses_destroyed_order_total",
    # NCEI impact — houses damaged
    "ncei_housesDamaged":                   "houses_damaged",
    "ncei_housesDamagedAmountOrder":        "houses_damaged_order",
    "ncei_housesDamagedTotal":              "houses_damaged_total",
    "ncei_housesDamagedAmountOrderTotal":   "houses_damaged_order_total",
    # NCEI — other
    "ncei_intensity":       "intensity",
    "ncei_tsunamiEventId":  "tsunami_event_id",
    "ncei_volcanoEventId":  "volcano_event_id",
}


def clean_merged(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the merged USGS+NCEI DataFrame.

    Returns a copy of df with:
      - impact columns coerced to float
      - duplicate USGS events removed (keep first match)
      - rows without magnitude dropped
      - a 'magnitude' convenience column (USGS value, NCEI fallback)
      - a 'year' convenience column
      - a 'depth_category' column (shallow / intermediate / deep)
      - a 'region' column parsed from ncei_locationName
    """
    df = df.copy()

    # 1. Coerce impact columns to numeric
    for col in IMPACT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in PHYSICS_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 2. Drop duplicate USGS events (one USGS quake matched to multiple NCEI records)
    # The id column may arrive as 'usgs_usgs_id' (double-prefix) or 'usgs_id'
    id_col = "usgs_usgs_id" if "usgs_usgs_id" in df.columns else "usgs_id"
    if id_col in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=[id_col], keep="first").reset_index(drop=True)
        print(f"Dropped {before - len(df)} duplicate USGS matches")

    # 3. Drop rows with no usable magnitude
    mag_missing = df["usgs_magnitude"].isna()
    df = df[~mag_missing].reset_index(drop=True)
    print(f"Kept {len(df)} rows with a valid magnitude")

    # 4. Add a single 'magnitude' column (USGS preferred, NCEI fallback)
    df["magnitude"] = df["usgs_magnitude"].fillna(
        pd.to_numeric(df.get("ncei_eqMagnitude"), errors="coerce")
    )

    # 5. Year column
    if "usgs_time" in df.columns:
        df["usgs_time"] = pd.to_datetime(df["usgs_time"], utc=True, errors="coerce")
        df["year"] = df["usgs_time"].dt.year
    elif "ncei_year" in df.columns:
        df["year"] = pd.to_numeric(df["ncei_year"], errors="coerce")

    # 6. Depth category (adjusted for more even count distribution)
    # 0–30 km: upper crust (very shallow); 30–150 km: lower crust/upper mantle; 150+ km: deep
    if "usgs_depth" in df.columns:
        df["depth_category"] = pd.cut(
            df["usgs_depth"],
            bins=[-np.inf, 30, 150, np.inf],
            labels=["shallow", "intermediate", "deep"],
        )

    # 7. Region from NCEI location name (everything after the last comma, or the whole string)
    if "ncei_locationName" in df.columns:
        df["region"] = df["ncei_locationName"].apply(_extract_region)

    # 8. Drop NCEI columns that duplicate USGS data (time, lat/lon, depth)
    cols_to_drop = [c for c in NCEI_DUPLICATE_COLS if c in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    # 9. Rename all columns to clean, consistent snake_case names
    df = df.rename(columns={k: v for k, v in COLUMN_RENAMES.items() if k in df.columns})

    return df


def _extract_region(location_name) -> str:
    """Extract the country/region part from an NCEI locationName string."""
    if pd.isna(location_name):
        return "Unknown"
    parts = str(location_name).split(",")
    return parts[-1].strip() if len(parts) > 1 else str(location_name).strip()
