# Assignment 7 App Guide

## Current Status

A7.4 Executive Overview is implemented over validated A7.2 Parquet/JSON artifacts. The remaining pages retain their staged scope; see the plan before beginning A7.5.

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

The Executive Overview presents frozen logistic final-holdout metrics, a development-OOF comparison, holdout lift and calibration diagnostics, and a selectable retrospective top-10/25/50 table. Logistic remains the pre-locked primary model; HistGradientBoosting is shown only as sensitivity analysis. No model is fit and no risk bands are defined in the app. The holdout table is an evaluation record, not a live forecast.

Explorer-only filters are wired to the A7.2 option artifact. No risk category is available because no presentation cutpoints were approved. A5 coverage states are `comparison_eligible` and `thin`.

Reset defaults are all metropolitan areas, all sectors, the latest descriptive year, all risk categories (currently unavailable), and all observed-gap statuses.

## Current Limitations

The Explorer, Model Performance, and Data Quality pages remain in their staged implementation phases. There is no map, deployment, live forecast, model fitting, or causal analysis. Overview metrics and ranked cases are retrospective and do not establish generalization beyond the single temporal holdout.
