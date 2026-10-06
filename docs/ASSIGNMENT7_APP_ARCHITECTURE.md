# Assignment 7 App Architecture

## Entry Point and Navigation

`streamlit_app.py` calls `dashboard.app.main`. The app sets Streamlit page configuration once, validates A7.2 artifacts, then defines five `st.Page` modules through Streamlit's `st.navigation` sidebar API.

## Page Modules

`dashboard/pages/` contains overview, explorer, performance, quality, and about modules. Each page loads shared metadata/options and only the necessary A7.2 table through cached data-access helpers; current page content is limited to A7.3 structure/placeholders.

## Data Flow and Cache

The app uses `dashboard.loader` exclusively for data access. Thin `st.cache_data` wrappers memoize validated metadata, filter options, health results, and immutable DataFrames. UI code does not open the canonical SQLite database, query raw/staging tables, or recompute scientific outputs.

## Reusable Components

`components.py` provides shared header/footer, primary-model label, gap explainer, coverage state, split labels, limitation/empty-state callouts, and UTF-8 CSV conversion. `filters.py` exposes Explorer-scoped controls using `dashboard_filter_options.json`; `state.py` sanitizes invalid session values and resets to documented defaults.

## Health Checks

`dashboard.health` validates required files, metadata version/fields, filter-option groups, readable Parquet datasets, and required columns. It returns structured checks for app startup and supports a CLI health report without launching Streamlit.

## Future Integration

Later A7 stages can add Plotly views to the corresponding page modules while retaining the fixed A6 populations and Explorer-only filter scope. The Explorer can host a future map only after its separately documented geography specification is approved. No map, Plotly chart, or production download is implemented in A7.3.
