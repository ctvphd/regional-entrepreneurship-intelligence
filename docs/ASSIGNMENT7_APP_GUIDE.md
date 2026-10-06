# Assignment 7 App Guide

## Current Status

A7.3 shell only. The five pages contain structural placeholders; substantive charts and page analytics are deferred to later A7 stages.

## Launch

From the repository root:

```powershell
uv run streamlit run streamlit_app.py
```

## Data Prerequisites

The validated A7.2 Parquet and JSON artifacts must exist under `data/dashboard/`. The app loads them only through the allow-listed dashboard loader and caches immutable reads with Streamlit `st.cache_data`.

## Rebuild

```powershell
uv run --offline python -m regional_entrepreneurship_intelligence.dashboard.run_data_layer
```

Validate artifacts without launching the UI:

```powershell
uv run --offline python -m regional_entrepreneurship_intelligence.dashboard.health
```

## Current Pages

- Executive Overview
- Regional & Industry Explorer
- Model Performance
- Data Quality & Limitations
- About / Methods / Sources

Explorer-only filters are wired to the A7.2 option artifact. No risk category is available because no presentation cutpoints were approved. A5 coverage states are `comparison_eligible` and `thin`.

Reset defaults are all metropolitan areas, all sectors, the latest descriptive year, all risk categories (currently unavailable), and all observed-gap statuses.

## Current Limitations

This is the A7.3 application shell. Final visualizations, substantive filtering/ranking, CSV downloads, and full-page analytics arrive in later A7 phases. There is no map, deployment, live forecast, model fitting, or causal analysis.
