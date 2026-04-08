# tests/test_merge.py
# Tests for the merge module.

import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from quakewatch.merge import merge_datasets


def make_usgs():
    return pd.DataFrame({
        "id":        ["eq1", "eq2", "eq3"],
        "time":      pd.to_datetime(["2010-01-12 21:53:00",
                                      "2015-04-25 06:11:00",
                                      "2020-06-01 12:00:00"], utc=True),
        "latitude":  [18.9, 28.2, -10.0],
        "longitude": [-72.0, 84.7, 160.0],
        "depth":     [13.0, 15.0, 33.0],
        "magnitude": [7.0, 7.8, 6.0],
        "place":     ["Haiti", "Nepal", "Pacific Ocean"],
        "sig":       [800, 850, 500],
        "mmi":       [8.0, 8.5, 6.0],
        "felt":      [5000, 2000, 100],
    })


def make_ncei():
    return pd.DataFrame({
        "year":    [2010, 2015],
        "month":   [1, 4],
        "day":     [12, 25],
        "date":    pd.to_datetime(["2010-01-12", "2015-04-25"], utc=True),
        "latitude":  [18.9, 28.2],
        "longitude": [-72.0, 84.7],
        "magnitude": [7.0, 7.8],
        "deaths":    [316000, 8964],
        "injuries":  [300000, 22000],
        "damage_millions_dollars": [8000, 5000],
        "houses_destroyed": [250000, 50000],
        "location_name": ["Haiti", "Nepal"],
    })


def test_merge_returns_same_length_as_usgs():
    usgs = make_usgs()
    ncei = make_ncei()
    result = merge_datasets(usgs, ncei)
    # Merged result should have the same number of rows as USGS (left join)
    assert len(result) == len(usgs)


def test_merge_adds_impact_columns():
    usgs = make_usgs()
    ncei = make_ncei()
    result = merge_datasets(usgs, ncei)
    assert "deaths" in result.columns
    assert "injuries" in result.columns
    assert "damage_millions_dollars" in result.columns


def test_merge_matches_haiti():
    usgs = make_usgs()
    ncei = make_ncei()
    result = merge_datasets(usgs, ncei)
    # The Haiti earthquake (eq1) should have deaths = 316000
    haiti_row = result[result["id"] == "eq1"]
    assert not haiti_row.empty
    assert haiti_row["deaths"].iloc[0] == 316000


def test_unmatched_usgs_rows_have_nan_deaths():
    usgs = make_usgs()
    ncei = make_ncei()
    result = merge_datasets(usgs, ncei)
    # eq3 (Pacific Ocean, 2020) has no NCEI match → deaths should be NaN
    pacific_row = result[result["id"] == "eq3"]
    assert pd.isna(pacific_row["deaths"].iloc[0])
