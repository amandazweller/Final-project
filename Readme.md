# 🌎 Earthquake Impact Analyzer

## Project Overview
This project aims to analyze global earthquake patterns and their real-world impacts by combining earthquake event data with disaster response data. We build a custom dataset using data from the Earthquake Catalog API and the  FEMA Open Data API. Our goal is to move beyond simply identifying where earthquakes occur and instead understand how they affect communities.


## Research Questions
The main questions motivating our analysis are:

- How does earthquake magnitude relate to real-world impact (e.g., disaster declarations)?
- Are certain regions more vulnerable to earthquake damage?
- Does earthquake depth influence the level of impact on affected areas?
- How does earthquake frequency vary over time and across geographic regions?


## Hypotheses
We expect to find that:

- Higher magnitude earthquakes are generally associated with greater disaster impact and more frequent FEMA disaster declarations.
- Geographic location plays a major role in determining impact, with more populated or vulnerable regions experiencing greater damage.
- Deeper earthquakes may result in less surface-level damage compared to shallow earthquakes.
- Earthquake activity will show regional clustering rather than being evenly distributed globally.



## Data Sources

### 1. USGS Earthquake Data
- Provides detailed earthquake event data including magnitude, depth, location (latitude/longitude), and timestamps.
- This dataset is essential for understanding the physical characteristics and patterns of earthquakes.

### 2. FEMA Disaster Data
- Provides information on disaster declarations, including type, location (state), and incident dates.
- This dataset allows us to measure the real-world impact of earthquakes through government response and aid.

### Why This Data Is Sufficient
By combining these two datasets, we can analyze both:
- **Earthquake characteristics** (magnitude, depth, location)
- **Impact outcomes** (disaster declarations, affected regions)

This allows us to directly connect seismic activity with real-world consequences.



## Custom Dataset Construction

Our dataset goes beyond a simple API pull by combining and transforming data from multiple sources.

### Steps:

1. **Data Collection**
   - Retrieve earthquake data from the USGS API.
   - Retrieve disaster declaration data from FEMA.

2. **Data Cleaning**
   - Convert timestamps into usable date formats
   - Handle missing or inconsistent values
   - Standardize location information (e.g., states, regions)

3. **Data Integration**
   - Merge datasets based on:
     - **Date proximity** (earthquake date vs. disaster declaration date)
     - **Geographic location** (state/region)
   - Since there is no shared unique identifier, this requires approximate matching.

4. **Feature Engineering**
   - Create new variables such as:
     - Earthquake magnitude vs. disaster occurrence
     - Frequency of disasters by region
     - Time differences between events and responses

### Why This Is Non-Trivial
- The datasets come from different sources with different formats
- There is no direct key to join them
- Matching requires thoughtful logic using time and location
- Additional variables must be created to enable meaningful analysis



## Project Goals
- Build a reusable Python package for earthquake data collection and analysis
- Explore patterns in earthquake activity and impact
- Provide meaningful insights into factors that influence disaster severity