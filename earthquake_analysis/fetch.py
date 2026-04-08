"""
fetch.py — Pull earthquake data from USGS and NOAA/NCEI APIs.

Two public functions:
    fetch_ncei(min_year, max_year)   → DataFrame of significant earthquakes with impact data
    fetch_usgs(start_date, end_date) → DataFrame of all USGS-detected earthquakes
"""

import time
import requests
import pandas as pd
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

NCEI_URL = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/earthquakes"
USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"


def fetch_ncei(min_year: int, max_year: int, min_magnitude: float = 0) -> pd.DataFrame:
    """
    Fetch all NOAA/NCEI significant earthquake records between min_year and max_year.

    Paginates automatically (API returns 25 records/page by default).
    Returns a DataFrame with impact columns: deaths, injuries, damageMillionsDollars, etc.
    Also builds a UTC 'time' column from the separate year/month/day columns.
    """
    params = {"minYear": min_year, "maxYear": max_year, "page": 1}
    if min_magnitude > 0:
        params["minMagnitude"] = min_magnitude

    all_items = []
    page = 1

    while True:
        params["page"] = page
        r = requests.get(NCEI_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        items = data.get("items", [])
        all_items.extend(items)
        total_pages = data.get("totalPages", 1)
        print(f"  NCEI page {page}/{total_pages} — {len(all_items)} records so far", end="\r")

        if page >= total_pages:
            break
        page += 1

    print(f"\nNCEI: fetched {len(all_items)} records ({min_year}–{max_year})")
    df = pd.DataFrame(all_items)

    # Build a proper UTC datetime from the separate year/month/day columns
    df["time"] = df.apply(_build_ncei_timestamp, axis=1)

    return df


def _build_ncei_timestamp(row) -> pd.Timestamp:
    """Convert NCEI year/month/day columns into a single UTC Timestamp."""
    try:
        year  = int(row["year"])
        month = int(row["month"]) if pd.notna(row.get("month")) else 1
        day   = int(row["day"])   if pd.notna(row.get("day"))   else 1
        return pd.Timestamp(year=year, month=month, day=day, tz="UTC")
    except Exception:
        return pd.NaT


def fetch_usgs(
    start_date: str,
    end_date: str,
    min_magnitude: float = 0,
    chunk_months: int = 1,
) -> pd.DataFrame:
    """
    Fetch USGS earthquake events between start_date and end_date.

    Chunks requests into `chunk_months`-sized windows to stay under the
    20,000-row-per-request API limit.

    Args:
        start_date:    ISO date string, e.g. "2000-01-01"
        end_date:      ISO date string, e.g. "2024-12-31"
        min_magnitude: Minimum magnitude filter (0 = all).
        chunk_months:  Window size per request (default 1 month).

    Returns a DataFrame with columns:
        usgs_id, time, latitude, longitude, depth, magnitude, place, sig, mmi, alert
    """
    start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    end   = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

    frames = []
    current = start

    while current < end:
        chunk_end = min(current + relativedelta(months=chunk_months), end)
        params = {
            "format":       "geojson",
            "starttime":    current.date().isoformat(),
            "endtime":      chunk_end.date().isoformat(),
            "minmagnitude": min_magnitude,
            "limit":        20000,
            "orderby":      "time-asc",
        }
        r = requests.get(USGS_URL, params=params, timeout=60)
        r.raise_for_status()
        features = r.json().get("features", [])

        rows = []
        for feat in features:
            props  = feat["properties"]
            coords = feat["geometry"]["coordinates"]
            rows.append({
                "usgs_id":   feat["id"],
                "time":      pd.Timestamp(props["time"], unit="ms", tz="UTC"),
                "latitude":  coords[1],
                "longitude": coords[0],
                "depth":     coords[2],
                "magnitude": props["mag"],
                "place":     props["place"],
                "sig":       props["sig"],
                "mmi":       props["mmi"],
                "alert":     props["alert"],
            })

        frames.append(pd.DataFrame(rows))
        print(f"  USGS {current.date()} → {chunk_end.date()}: {len(rows)} records", end="\r")
        current = chunk_end
        time.sleep(0.5)  # be polite to the API

    df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["usgs_id"])
    print(f"\nUSGS: fetched {len(df)} records ({start_date} → {end_date})")
    return df
