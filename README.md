# earthquake-analysis

A Python package for analyzing global earthquake patterns and real-world human impact, built for a data science final project.

## Research Questions

1. **Magnitude → Impact** — Does a higher magnitude mean more deaths and damage? Is there a threshold where earthquakes become truly deadly?
2. **Depth → Damage** — Does focal depth influence how destructive an earthquake is?
3. **Regional Vulnerability** — Which regions are hit hardest? Are some areas disproportionately vulnerable even for similar-sized quakes?
4. **Trends Over Time** — Has the human cost or property damage of earthquakes changed year over year?

## Data Sources

| Source | API | Coverage | Key columns |
|--------|-----|----------|-------------|
| **USGS Earthquake Hazards** | `https://earthquake.usgs.gov/fdsnws/event/1/query` | All detected events; chunked in 1-month windows to stay under the 20 k-row limit | magnitude, depth, lat/lon, time, sig, mmi, alert |
| **NOAA/NCEI HazEL** | `https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/earthquakes` | ~5,700 significant earthquakes; paginated (25 records/page) | deaths, injuries, damageMillionsDollars, housesDestroyed |

**Merge strategy:** For each NCEI record, find the best-matching USGS event within ±3 days and ±1° lat/lon, then pick the closest magnitude match. USGS is the primary source; NCEI enriches it with impact data.

## Package Structure

```
earthquake_analysis/
├── earthquake_analysis/
│   ├── __init__.py      # Public API
│   ├── fetch.py         # fetch_ncei(), fetch_usgs()
│   ├── merge.py         # merge_usgs_ncei()
│   ├── clean.py         # clean_merged(), make_analysis_subset()
│   └── analyze.py       # analysis functions for Q1–Q4
├── scripts/
│   └── run_pipeline.py  # Fetch → Merge → Clean → Subset → Save
├── data/                # Created by the pipeline (git-ignored)
├── app.py               # Streamlit dashboard
├── pyproject.toml
└── README.md
```

## Quick Start

### 1. Install

```bash
pip install -e ".[dev]"
```

### 2. Run the data pipeline

This fetches data from both APIs, merges them, cleans the result, and saves CSVs to `data/`.

```bash
python scripts/run_pipeline.py
```

The pipeline produces:
- `data/ncei_raw.csv` — raw NCEI fetch
- `data/usgs_raw.csv` — raw USGS fetch
- `data/merged.csv` — after approximate matching
- `data/cleaned.csv` — full cleaned dataset (all matched rows)
- `data/analysis_subset.csv` — rows with deaths, magnitude, and damage_order present; columns >80% null dropped ← used by the app

> **Note:** Fetching 25 years of USGS data takes several minutes due to API rate limiting. The NCEI fetch is fast (paginated, ~5 k records total). The USGS fetch takes much longer as it contains ~3 million records.

### 3. Launch the Streamlit app

```bash
streamlit run app.py
```

### 4. Use the package directly

```python
from earthquake_analysis import (
    fetch_ncei, fetch_usgs,
    merge_usgs_ncei, clean_merged, make_analysis_subset,
    magnitude_vs_impact, yearly_trends,
)

# Fetch
df_ncei = fetch_ncei(min_year=2010, max_year=2024)
df_usgs = fetch_usgs("2010-01-01", "2024-12-31")

# Merge, clean, and build analysis-ready subset
merged  = merge_usgs_ncei(df_usgs, df_ncei)
cleaned = clean_merged(merged)
subset  = make_analysis_subset(cleaned)

# Analyze
print(magnitude_vs_impact(subset))
print(yearly_trends(subset))
```

## Module Reference

### `fetch.py`

| Function | Description |
|----------|-------------|
| `fetch_ncei(min_year, max_year)` | Paginates through NCEI HazEL API, builds UTC `time` column |
| `fetch_usgs(start_date, end_date)` | Chunks requests monthly to stay under 20 k limit |

### `merge.py`

| Function | Description |
|----------|-------------|
| `merge_usgs_ncei(df_usgs, df_ncei)` | Approximate match on time ± 3 days and location ± 1°; best magnitude match wins |

### `clean.py`

| Function | Description |
|----------|-------------|
| `clean_merged(df)` | Coerces numerics, drops dupes and rows missing time/location, adds `magnitude`, `year`, `depth_category`, `region`; renames all columns to snake_case |
| `make_analysis_subset(df)` | Filters to rows with `deaths`, `magnitude`, and `damage_order` present; drops columns >80% null |

### `analyze.py`

| Function | Research Q | Returns |
|----------|------------|---------|
| `magnitude_vs_impact(df)` | Q1 | Deaths/damage by magnitude bin |
| `deadly_threshold(df)` | Q1 | Magnitude where 50%+ of quakes cause deaths |
| `depth_vs_impact(df)` | Q2 | Median impact by depth category |
| `regional_impact(df)` | Q3 | Deaths/damage by region |
| `vulnerability_index(df)` | Q3 | Deaths-per-event / median magnitude |
| `yearly_trends(df)` | Q4 | Annual totals |
| `rolling_average(yearly_df)` | Q4 | Adds 5-year rolling means |

## `.gitignore` additions

```
data/
__pycache__/
*.egg-info/
.streamlit/
```

## Read More
- [GitHub Pages Site](https://amandazweller.github.io/Final-project/)
- [Tutorial](https://amandazweller.github.io/Final-project/tutorial.html)
- [Final Report](https://amandazweller.github.io/Final-project/report.html)
