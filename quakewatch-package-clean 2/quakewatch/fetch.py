# quakewatch/fetch.py
#
# This module fetches earthquake data from two public APIs:
#   1. USGS Earthquake Hazards API  (https://earthquake.usgs.gov)
#   2. NOAA/NCEI HazEL API          (https://www.ngdc.noaa.gov/hazel)
#
# No API keys are needed for either source.

import requests
import pandas as pd
from datetime import datetime, timedelta
import time


# ---------------------------------------------------------------------------
# USGS
# ---------------------------------------------------------------------------

USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# The USGS API returns at most 20,000 rows per request.
# To get more data we break the date range into smaller chunks.
USGS_CHUNK_DAYS = 30  # fetch 30 days at a time


def fetch_usgs(
    start_date: str,
    end_date: str,
    min_magnitude: float = 0.0,   # 0 = include all magnitudes
    max_magnitude: float = 10.0,
) -> pd.DataFrame:
    """
    Download earthquake records from the USGS API.

    Parameters
    ----------
    start_date : str
        First date to include, e.g. "2000-01-01".
    end_date : str
        Last date to include, e.g. "2023-12-31".
    min_magnitude : float
        Smallest magnitude to keep (0 = no lower limit).
    max_magnitude : float
        Largest magnitude to keep (10 = no upper limit).

    Returns
    -------
    pd.DataFrame
        One row per earthquake with columns:
        id, time, latitude, longitude, depth, magnitude,
        place, sig, mmi, felt.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end   = datetime.strptime(end_date,   "%Y-%m-%d")

    all_chunks = []
    chunk_start = start

    print(f"Fetching USGS data from {start_date} to {end_date} ...")

    while chunk_start < end:
        chunk_end = min(chunk_start + timedelta(days=USGS_CHUNK_DAYS), end)

        params = {
            "format":      "geojson",
            "starttime":   chunk_start.strftime("%Y-%m-%d"),
            "endtime":     chunk_end.strftime("%Y-%m-%d"),
            "minmagnitude": min_magnitude,
            "maxmagnitude": max_magnitude,
            "orderby":     "time",
            "limit":       20000,
        }

        response = requests.get(USGS_URL, params=params, timeout=60)
        response.raise_for_status()   # raises an error if the request failed

        data = response.json()
        features = data.get("features", [])

        if features:
            rows = []
            for feature in features:
                props = feature["properties"]
                coords = feature["geometry"]["coordinates"]  # [lon, lat, depth]
                rows.append({
                    "id":        feature["id"],
                    # USGS gives time as milliseconds since 1970 — convert to datetime
                    "time":      pd.to_datetime(props["time"], unit="ms", utc=True),
                    "latitude":  coords[1],
                    "longitude": coords[0],
                    "depth":     coords[2],
                    "magnitude": props.get("mag"),
                    "place":     props.get("place"),
                    "sig":       props.get("sig"),    # significance score (0-1000)
                    "mmi":       props.get("mmi"),    # max intensity (Modified Mercalli)
                    "felt":      props.get("felt"),   # number of people who reported feeling it
                })
            chunk_df = pd.DataFrame(rows)
            all_chunks.append(chunk_df)
            print(f"  {chunk_start.date()} → {chunk_end.date()} : {len(rows):,} rows")
        else:
            print(f"  {chunk_start.date()} → {chunk_end.date()} : 0 rows")

        chunk_start = chunk_end + timedelta(days=1)

    if not all_chunks:
        print("No USGS data found for this date range.")
        return pd.DataFrame()

    df = pd.concat(all_chunks, ignore_index=True)
    print(f"USGS total: {len(df):,} rows\n")
    return df


# ---------------------------------------------------------------------------
# NOAA / NCEI
# ---------------------------------------------------------------------------

NCEI_URL = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/earthquakes"

def fetch_ncei(min_year: int, max_year: int, min_magnitude: float = 0) -> pd.DataFrame:
    params = {
        "minYear": min_year,
        "maxYear": max_year,
        "page": 1,
    }
    if min_magnitude > 0:
        params["minMagnitude"] = min_magnitude

    all_items = []
    page = 1

    while True:
        params["page"] = page
        r = requests.get(NCEI_URL, params=params)
        r.raise_for_status()
        data = r.json()

        items = data.get("items", [])
        all_items.extend(items)

        total_pages = data.get("totalPages", 1)
        print(f"  Page {page}/{total_pages} — {len(all_items)} records so far", end="\r")

        if page >= total_pages:
            break
        page += 1
    

    print(f"\nDone. Fetched {len(all_items)} total records ({min_year}–{max_year})")
    
    return pd.DataFrame(all_items)
