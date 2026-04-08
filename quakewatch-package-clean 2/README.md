# 🌍 QuakeWatch

**QuakeWatch** is a Python package for analyzing global earthquake patterns and their real-world impact — built as a data science final project.

## Research Questions
1. How does earthquake magnitude relate to real-world impact (deaths, damage)?
2. Does earthquake depth influence damage severity?
3. Which regions are most seismically vulnerable?
4. How has earthquake activity changed over time?

## Data Sources
- **USGS Earthquake Hazards API** — magnitude, depth, location, significance score, MMI
- **NOAA/NCEI HazEL API** — significant earthquakes with deaths, injuries, damage costs

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from quakewatch import fetch_usgs, fetch_ncei, merge_datasets, analyze, plot

# 1. Fetch data
usgs = fetch_usgs(start_date="2000-01-01", end_date="2023-12-31", min_magnitude=4.0)
ncei = fetch_ncei()

# 2. Merge datasets
df = merge_datasets(usgs, ncei)

# 3. Analyze
summary = analyze.summary_stats(df)

# 4. Plot
plot.magnitude_vs_deaths(df)
```

## Project Structure

```
quakewatch/
├── quakewatch/         # Main package
│   ├── fetch.py        # Data fetching from APIs
│   ├── clean.py        # Data cleaning
│   ├── merge.py        # Merging USGS + NCEI
│   ├── analyze.py      # Analysis functions
│   └── plot.py         # Visualization functions
├── scripts/
│   └── clean_data.py   # Standalone cleaning script
├── docs/               # Quarto documentation
├── app.py              # Streamlit app
└── pyproject.toml
```

## Documentation

Documentation is hosted on GitHub Pages (link coming soon).

## Running the App

```bash
streamlit run app.py
```
