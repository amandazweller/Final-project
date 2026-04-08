"""
earthquake_analysis
===================
A Python package for analyzing global earthquake patterns and real-world impact.

Modules
-------
fetch   — Pull data from USGS and NOAA/NCEI APIs
merge   — Approximate-match the two sources into one dataset
clean   — Clean and enrich the merged DataFrame
analyze — Answer the four research questions
"""

from .fetch   import fetch_ncei, fetch_usgs
from .merge   import merge_usgs_ncei
from .clean   import clean_merged
from .analyze import (
    magnitude_vs_impact,
    deadly_threshold,
    depth_vs_impact,
    regional_impact,
    vulnerability_index,
    yearly_trends,
    rolling_average,
)

__version__ = "0.1.0"
__all__ = [
    "fetch_ncei",
    "fetch_usgs",
    "merge_usgs_ncei",
    "clean_merged",
    "magnitude_vs_impact",
    "deadly_threshold",
    "depth_vs_impact",
    "regional_impact",
    "vulnerability_index",
    "yearly_trends",
    "rolling_average",
]
