# tests/test_clean.py
# Tests for clean_merged() — the single cleaning function that runs
# on the already-merged USGS + NCEI DataFrame.
#
# Run with: pytest tests/

import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from quakewatch.clean import clean_merged


def make_fake_merged():
    """
    Create a small fake merged DataFrame that mimics the output of
    merge_datasets() — with some intentional problems to clean.
    """
    return pd.DataFrame({
        "id":        ["eq1", "eq2", "eq3", "eq4", "eq5"],
        "time":      pd.to_datetime(
                         ["2020-01-01", "2020-06-15", None, "2021-03-01", "2021-09-01"],
                         utc=True),
        "latitude":  [35.0, None, 40.0, 18.9,  200.0],   # None + 200 are bad
        "longitude": [139.0, 120.0, 20.0, -72.0, 50.0],
        "depth":     [10.0, -5.0, 30.0, 13.0, 20.0],     # -5 is bad
        "magnitude": [5.5, 7.0, None, 7.0, 6.0],          # None is bad
        "place":     ["Tokyo", "Shanghai", "Athens", "Haiti", "Somewhere"],
        "sig":       [600, 900, 400, 800, 500],
        "mmi":       [6.0, 8.0, 5.0, 8.5, 6.5],
        "felt":      [100, 500, None, 5000, 200],
        # Impact columns from NCEI — some matched (real values), some not (NaN)
        "deaths":              [0.0, np.nan, np.nan, 316000.0, np.nan],
        "injuries":            [0.0, np.nan, np.nan, 300000.0, np.nan],
        "damage_millions_dollars": [50.0, np.nan, np.nan, 8000.0, np.nan],
        "houses_destroyed":    [0.0, np.nan, np.nan, 250000.0, np.nan],
        "ncei_magnitude":      [np.nan, np.nan, np.nan, 7.0, np.nan],
        "ncei_location":       [None, None, None, "Haiti", None],
    })


def test_drops_rows_missing_location():
    df = clean_merged(make_fake_merged())
    assert df["latitude"].isna().sum() == 0
    assert df["longitude"].isna().sum() == 0


def test_drops_rows_missing_time():
    df = clean_merged(make_fake_merged())
    assert df["time"].isna().sum() == 0


def test_drops_rows_missing_magnitude():
    df = clean_merged(make_fake_merged())
    assert df["magnitude"].isna().sum() == 0


def test_removes_negative_depth():
    df = clean_merged(make_fake_merged())
    assert (df["depth"] < 0).sum() == 0


def test_removes_impossible_latitude():
    df = clean_merged(make_fake_merged())
    # latitude=200 should be removed
    assert df["latitude"].between(-90, 90).all()


def test_fills_unmatched_impact_with_zero():
    df = clean_merged(make_fake_merged())
    # All NaN impact values should now be 0
    assert df["deaths"].isna().sum() == 0
    assert df["injuries"].isna().sum() == 0


def test_index_is_reset():
    df = clean_merged(make_fake_merged())
    # After dropping rows, index should be 0, 1, 2, ... with no gaps
    assert list(df.index) == list(range(len(df)))
