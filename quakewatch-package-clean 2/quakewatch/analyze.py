# quakewatch/analyze.py
#
# Analysis functions that answer the four research questions:
#   1. Magnitude vs. real-world impact
#   2. Depth vs. damage severity
#   3. Most seismically vulnerable regions
#   4. Earthquake activity over time

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# 1. Summary statistics
# ---------------------------------------------------------------------------

def summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return basic summary statistics for numeric columns.

    Parameters
    ----------
    df : pd.DataFrame
        Merged earthquake DataFrame.

    Returns
    -------
    pd.DataFrame
        Descriptive stats (count, mean, std, min, max, etc.)
    """
    numeric_cols = ["magnitude", "depth", "deaths", "injuries",
                    "damage_millions_dollars", "sig", "mmi", "felt"]
    # Only keep columns that actually exist
    cols = [c for c in numeric_cols if c in df.columns]
    return df[cols].describe().round(2)


# ---------------------------------------------------------------------------
# 2. Magnitude vs. impact
# ---------------------------------------------------------------------------

def magnitude_impact_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the correlation between magnitude and each impact metric.

    A higher correlation means magnitude is a better predictor of that impact.

    Parameters
    ----------
    df : pd.DataFrame
        Merged earthquake DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['impact_metric', 'correlation_with_magnitude'].
    """
    impact_cols = ["deaths", "injuries", "damage_millions_dollars", "houses_destroyed", "sig"]
    results = []
    for col in impact_cols:
        if col in df.columns:
            # Only use rows where both values are non-null
            valid = df[["magnitude", col]].dropna()
            if len(valid) > 1:
                corr = valid["magnitude"].corr(valid[col])
            else:
                corr = np.nan
            results.append({"impact_metric": col, "correlation_with_magnitude": round(corr, 3)})
    return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# 3. Depth categories
# ---------------------------------------------------------------------------

def add_depth_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'depth_category' column based on standard seismological depth ranges.

    Categories
    ----------
    - Shallow  :  0 – 70 km
    - Intermediate : 70 – 300 km
    - Deep     : > 300 km

    Parameters
    ----------
    df : pd.DataFrame
        Earthquake DataFrame with a 'depth' column.

    Returns
    -------
    pd.DataFrame
        Same DataFrame with a new 'depth_category' column.
    """
    df = df.copy()
    bins   = [0,  70, 300, 9999]
    labels = ["Shallow", "Intermediate", "Deep"]
    df["depth_category"] = pd.cut(df["depth"], bins=bins, labels=labels, right=True)
    return df


def depth_vs_impact(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare average impact metrics across depth categories.

    Parameters
    ----------
    df : pd.DataFrame
        Earthquake DataFrame (depth_category column added by add_depth_category).

    Returns
    -------
    pd.DataFrame
        Mean deaths, injuries, and damage grouped by depth category.
    """
    if "depth_category" not in df.columns:
        df = add_depth_category(df)

    impact_cols = [c for c in ["deaths", "injuries", "damage_millions_dollars"] if c in df.columns]
    return (
        df.groupby("depth_category", observed=True)[impact_cols]
        .mean()
        .round(2)
        .reset_index()
    )


# ---------------------------------------------------------------------------
# 4. Regional vulnerability
# ---------------------------------------------------------------------------

def top_countries_by_deaths(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Return the top N countries by total earthquake-related deaths.

    Parameters
    ----------
    df : pd.DataFrame
        Merged earthquake DataFrame with a 'ncei_location' or 'country' column.
    n : int
        Number of countries to return.

    Returns
    -------
    pd.DataFrame
        Columns: country/location, total_deaths, event_count.
    """
    # Use 'ncei_location' if 'country' is not available
    location_col = "country" if "country" in df.columns else "ncei_location"
    if location_col not in df.columns or "deaths" not in df.columns:
        print("Need a location and deaths column for this analysis.")
        return pd.DataFrame()

    result = (
        df.groupby(location_col)
        .agg(total_deaths=("deaths", "sum"), event_count=("deaths", "count"))
        .sort_values("total_deaths", ascending=False)
        .head(n)
        .reset_index()
    )
    return result


def earthquakes_per_region(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Count earthquakes per USGS 'place' region (top N most active).

    Parameters
    ----------
    df : pd.DataFrame
        USGS earthquake DataFrame with a 'place' column.
    n : int
        Number of regions to return.

    Returns
    -------
    pd.DataFrame
        Columns: place, earthquake_count.
    """
    if "place" not in df.columns:
        return pd.DataFrame()
    return (
        df["place"]
        .value_counts()
        .head(n)
        .rename_axis("place")
        .reset_index(name="earthquake_count")
    )


# ---------------------------------------------------------------------------
# 5. Trends over time
# ---------------------------------------------------------------------------

def earthquakes_per_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count earthquakes per year and calculate the mean magnitude per year.

    Parameters
    ----------
    df : pd.DataFrame
        Earthquake DataFrame with a 'time' column (datetime).

    Returns
    -------
    pd.DataFrame
        Columns: year, earthquake_count, mean_magnitude.
    """
    df = df.copy()
    df["year"] = pd.to_datetime(df["time"], utc=True).dt.year
    result = (
        df.groupby("year")
        .agg(earthquake_count=("magnitude", "count"), mean_magnitude=("magnitude", "mean"))
        .round(2)
        .reset_index()
    )
    return result


def magnitude_distribution(df: pd.DataFrame, bins: int = 20) -> pd.Series:
    """
    Return a histogram-style count of earthquakes by magnitude bin.

    Parameters
    ----------
    df : pd.DataFrame
        Earthquake DataFrame with a 'magnitude' column.
    bins : int
        Number of magnitude bins.

    Returns
    -------
    pd.Series
        Index = magnitude bin labels, values = earthquake counts.
    """
    return pd.cut(df["magnitude"], bins=bins).value_counts().sort_index()
