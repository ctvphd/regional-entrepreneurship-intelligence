# Assignment 7 App Architecture

## Entry Point and Navigation

`streamlit_app.py` calls `dashboard.app.main`. The app sets Streamlit page configuration once, validates A7.2 artifacts, then defines five `st.Page` modules through Streamlit's `st.navigation` sidebar API.

## Page Modules

`dashboard/pages/` contains overview, explorer, performance, quality, and about modules. A7.4 Executive Overview, A7.5 Explorer, A7.6 Model Performance, and A7.7 Data Quality are implemented over validated A7.2 artifacts; Quality also reads finalized A5/A6 reporting tables for frozen selection and generalization audits. About remains a separate, non-finalized page.

## Data Flow and Cache

The app uses `dashboard.loader` exclusively for data access. Thin `st.cache_data` wrappers memoize validated metadata, filter options, health results, and immutable DataFrames. UI code does not open the canonical SQLite database, query raw/staging tables, or recompute scientific outputs.

## Reusable Components

`components.py` provides shared header/footer, primary-model label, gap explainer, coverage state, split labels, limitation/empty-state callouts, and UTF-8 CSV conversion. `filters.py` exposes Explorer-scoped controls using `dashboard_filter_options.json`; `state.py` sanitizes invalid session values and resets to documented defaults.

## Health Checks

`dashboard.health` validates required files, metadata version/fields, filter-option groups, readable Parquet datasets, and required columns. It returns structured checks for app startup and supports a CLI health report without launching Streamlit.

## Future Integration

The implemented Overview and Performance Plotly views preserve fixed A6 populations; Explorer filters remain Explorer-only. Performance PR/ROC points use the narrow deterministic display transformation approved in `ASSIGNMENT7_DATA_CONTRACTS.md`, without fitting or reported-metric recomputation. Quality communicates source-backed coverage and limitations without altering analytics. The Explorer can host a future map only after its separately documented geography specification is approved; mapping and deployment remain deferred.
