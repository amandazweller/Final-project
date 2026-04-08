# tests/test_analyze.py
# Tests for the analyze module.

import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from quakewatch import analyze


def make_fake_merged():
    """Create a small fake merged DataFrame for testing analysis functions."""
    return pd.DataFrame({
        "time":       pd.to_datetime([
            "2000-03-01", "2005-07-15", "2010-01-12",
            "2015-04-25", "2020-11-30"
        ], utc=True),
        "latitude":   [38.3, 35.0, 28.0, -12.0, 37.0],
        "longitude":  [142.4, 110.0, 84.0, -76.0, 22.0],
        "depth":      [10.0, 200.0, 500.0, 35.0, 80.0],
        "magnitude":  [9.0, 6.5, 7.8, 6.0, 5.5],
        "place":      ["Japan", "China", "Nepal", "Peru", "Greece"],
        "deaths":     [15894, 87587, 8964, 0, 2],
        "injuries":   [5000, 374000, 22000, 100, 20],
        "damage_millions_dollars": [210000, 86000, 5000, 100, 50],
        "houses_destroyed": [120000, 15000, 50000, 0, 10],
        "ncei_location": ["Japan", "China", "Nepal", "Peru", "Greece"],
        "sig":        [900, 850, 800, 600, 400],
        "mmi":        [9.0, 8.5, 8.0, 7.5, 6.0],
    })


def test_summary_stats_returns_dataframe():
    df = make_fake_merged()
    result = analyze.summary_stats(df)
    assert isinstance(result, pd.DataFrame)
    assert "magnitude" in result.columns


def test_magnitude_impact_correlation_returns_correlations():
    df = make_fake_merged()
    result = analyze.magnitude_impact_correlation(df)
    assert "correlation_with_magnitude" in result.columns
    # All correlations should be between -1 and 1
    assert result["correlation_with_magnitude"].dropna().between(-1, 1).all()


def test_add_depth_category_creates_column():
    df = make_fake_merged()
    result = analyze.add_depth_category(df)
    assert "depth_category" in result.columns
    # depth=10 → Shallow, depth=200 → Intermediate, depth=500 → Deep
    cats = result["depth_category"].astype(str).tolist()
    assert "Shallow" in cats
    assert "Intermediate" in cats
    assert "Deep" in cats


def test_earthquakes_per_year_has_correct_years():
    df = make_fake_merged()
    result = analyze.earthquakes_per_year(df)
    assert "year" in result.columns
    assert "earthquake_count" in result.columns
    assert set(result["year"]) == {2000, 2005, 2010, 2015, 2020}


def test_top_countries_by_deaths_is_sorted():
    df = make_fake_merged()
    result = analyze.top_countries_by_deaths(df, n=5)
    # Should be sorted descending by total_deaths
    deaths = result["total_deaths"].tolist()
    assert deaths == sorted(deaths, reverse=True)
