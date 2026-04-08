# app.py
#
# QuakeWatch — Streamlit Web App
#
# Run with:
#   streamlit run app.py
#
# The app lets users:
#   • Load pre-saved data OR fetch fresh data from the APIs
#   • Explore the four research questions interactively

import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from quakewatch.fetch import fetch_usgs, fetch_ncei
from quakewatch.clean import clean_merged
from quakewatch.merge import merge_datasets
from quakewatch import analyze, plot

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuakeWatch",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 QuakeWatch — Global Earthquake Analysis")
st.markdown(
    "Explore global earthquake patterns and their real-world impact "
    "using data from **USGS** and **NOAA/NCEI**."
)

# ── Sidebar: data loading options ────────────────────────────────────────────
st.sidebar.header("Data Settings")

# Try to load pre-saved data by default (much faster than fetching)
CACHE_PATH = os.path.join(os.path.dirname(__file__), "data", "merged_earthquakes.csv")

data_source = st.sidebar.radio(
    "Data source",
    options=["Load saved data (fast)", "Fetch fresh from API (slow)"],
)


@st.cache_data(show_spinner="Loading data...")
def load_saved_data(path: str) -> pd.DataFrame:
    """Load data from a CSV file (cached so it only reads once)."""
    return pd.read_csv(path, parse_dates=["time"])


@st.cache_data(show_spinner="Fetching from APIs... this may take a few minutes.")
def fetch_and_merge(start: str, end: str, min_mag: float) -> pd.DataFrame:
    """Fetch, clean, and merge data from USGS and NCEI APIs."""
    usgs = fetch_usgs(start, end, min_mag)
    ncei = fetch_ncei()
    return clean_merged(merge_datasets(usgs, ncei))


# ── Load data ────────────────────────────────────────────────────────────────
df = None

if data_source == "Load saved data (fast)":
    if os.path.exists(CACHE_PATH):
        df = load_saved_data(CACHE_PATH)
        st.sidebar.success(f"Loaded {len(df):,} rows from file.")
    else:
        st.sidebar.warning(
            "No saved data found at `data/merged_earthquakes.csv`.\n\n"
            "Run `python scripts/clean_data.py` first, or switch to API fetch."
        )

else:
    st.sidebar.markdown("**API fetch settings**")
    start_date = st.sidebar.text_input("Start date", "2010-01-01")
    end_date   = st.sidebar.text_input("End date",   "2023-12-31")
    min_mag    = st.sidebar.slider("Minimum magnitude", 0.0, 9.0, 4.0, step=0.5)

    if st.sidebar.button("Fetch data"):
        df = fetch_and_merge(start_date, end_date, min_mag)
        st.sidebar.success(f"Fetched {len(df):,} rows.")

# ── Main content ─────────────────────────────────────────────────────────────
if df is None:
    st.info("👈 Use the sidebar to load or fetch data to get started.")
    st.stop()

# ── Tabs for each research question ──────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "💥 Magnitude vs. Impact",
    "⬇️ Depth vs. Damage",
    "🗺️ Regional Vulnerability",
    "📅 Trends Over Time",
])

# ── Tab 1: Overview ───────────────────────────────────────────────────────────
with tab1:
    st.subheader("Dataset Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Earthquakes", f"{len(df):,}")
    col2.metric("With Death Records", f"{df['deaths'].notna().sum():,}" if "deaths" in df.columns else "N/A")
    col3.metric("Max Magnitude", f"{df['magnitude'].max():.1f}" if "magnitude" in df.columns else "N/A")
    col4.metric("Date Range", f"{pd.to_datetime(df['time']).dt.year.min()} – {pd.to_datetime(df['time']).dt.year.max()}")

    st.markdown("---")
    st.subheader("Summary Statistics")
    st.dataframe(analyze.summary_stats(df), use_container_width=True)

    st.subheader("Magnitude Distribution")
    fig = plot.magnitude_histogram(df)
    st.pyplot(fig)
    plt.close(fig)

# ── Tab 2: Magnitude vs. Impact ───────────────────────────────────────────────
with tab2:
    st.subheader("Research Question 1: Does magnitude predict real-world impact?")

    if "deaths" in df.columns:
        col_a, col_b = st.columns([2, 1])
        with col_a:
            fig = plot.magnitude_vs_deaths(df)
            st.pyplot(fig)
            plt.close(fig)
        with col_b:
            st.markdown("**Correlations with Magnitude**")
            corr_df = analyze.magnitude_impact_correlation(df)
            st.dataframe(corr_df, use_container_width=True)

        st.subheader("Correlation Heatmap")
        fig = plot.correlation_heatmap(df)
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.warning("Impact columns not found. Make sure you're using the merged dataset.")

# ── Tab 3: Depth vs. Damage ───────────────────────────────────────────────────
with tab3:
    st.subheader("Research Question 2: Does depth influence damage severity?")

    df_depth = analyze.add_depth_category(df)
    depth_impact = analyze.depth_vs_impact(df_depth)

    st.markdown(
        "Earthquakes are classified as **Shallow** (0–70 km), "
        "**Intermediate** (70–300 km), or **Deep** (>300 km)."
    )

    st.dataframe(depth_impact, use_container_width=True)

    if not depth_impact.empty:
        fig = plot.depth_vs_impact_bar(depth_impact)
        st.pyplot(fig)
        plt.close(fig)

# ── Tab 4: Regional Vulnerability ────────────────────────────────────────────
with tab4:
    st.subheader("Research Question 3: Which regions are most seismically vulnerable?")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Top regions by earthquake count (USGS)**")
        region_df = analyze.earthquakes_per_region(df, n=10)
        st.dataframe(region_df, use_container_width=True)

    with col_b:
        if "deaths" in df.columns:
            st.markdown("**Top regions by total deaths (NCEI)**")
            deaths_df = analyze.top_countries_by_deaths(df, n=10)
            st.dataframe(deaths_df, use_container_width=True)

    if "deaths" in df.columns and not deaths_df.empty:
        fig = plot.top_countries_bar(deaths_df)
        st.pyplot(fig)
        plt.close(fig)

# ── Tab 5: Trends Over Time ───────────────────────────────────────────────────
with tab5:
    st.subheader("Research Question 4: How has earthquake activity changed over time?")

    yearly = analyze.earthquakes_per_year(df)

    fig = plot.earthquakes_per_year_line(yearly)
    st.pyplot(fig)
    plt.close(fig)

    st.dataframe(yearly, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Data: USGS Earthquake Hazards Program & NOAA/NCEI HazEL | Built with QuakeWatch")
