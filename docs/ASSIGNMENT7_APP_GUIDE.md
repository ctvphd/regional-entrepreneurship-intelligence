# Assignment 7 App Guide

## Current Status

A7.4 Executive Overview, A7.5 Regional & Industry Explorer, A7.6 Model Performance & Diagnostics, A7.7 Data Quality & Limitations, and A7.8 visualization refinement are implemented over validated A7.2 artifacts and finalized A5/A6 reports. A7.9 and A7.10 remain.

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

The Regional & Industry Explorer provides searchable MSA, sector, descriptive-year, historical-gap, and exact-key evaluation-prediction filters. Its default is all MSAs/sectors, the latest descriptive year, no gap restriction, no prediction-only restriction, and a top-10 final-holdout ranking. Reset restores those defaults. Observed/expected startup rates, alignment and development-OOF gap history, employment growth, and t-to-t+3 retrospective logistic records are presented separately with null-aware empty states. Prediction split and predictor year are explicit; a development OOF ranking is never combined with final holdout. A5 coverage labels are `comparison_eligible` and `thin`, and `thin` is a descriptive coverage warning rather than model confidence. The filtered UTF-8 CSV contains selected A7.2 panel rows, metadata context, and any exact-key attached prediction fields; actual target gaps are named retrospective. Risk categories remain unavailable.

Explorer-only filters are wired to the A7.2 option artifact. No risk category is available because no presentation cutpoints were approved. A5 coverage states are `comparison_eligible` and `thin`.

The Model Performance page presents fixed holdout logistic AP, prevalence,
ROC-AUC, Brier, recall, precision, F1, and top-decile lift from
`dashboard_model_summary`. It compares Development OOF with the final
temporal holdout and compares the prevalence benchmark, logistic primary, and
HGB sensitivity separately by split. Random Forest is shown only if a
finalized metric row is present; it is absent from the current A7.2 model set.
Explorer filters do not affect this page. Brier direction is lower-is-better;
AP is interpreted against prevalence rather than as accuracy.

PR/ROC point coordinates are constructed deterministically from unchanged
frozen predictions and actual labels, separately by evaluation split, under
the A7.6 display-only allowance in `ASSIGNMENT7_DATA_CONTRACTS.md`. There is
no refit, threshold selection, probability change, or summary-metric
recalculation. Calibration uses the published reliability bins with no
recalibration; lift uses the fixed summary values. Year and MSA-size charts
use the finalized subgroup artifacts. Sector AP/ROC-AUC suppression is
preserved; the source `sufficient_sample_flag` governs the AP chart and
suppressed cells stay blank in the sortable table. A7.6 lineage is recorded
in `ASSIGNMENT7_SOURCE_LINEAGE.md`.

Reset defaults are all metropolitan areas, all sectors, the latest descriptive year, all risk categories (currently unavailable), and all observed-gap statuses.

## Current Limitations

Data Quality & Limitations presents the 381-area A7.2 coverage inventory, A5
comparison screen, finalized A6 complete-case selection audit, sector sample
support and metric suppression, fixed MSA-size and unseen-MSA diagnostics,
source catalog, lineage, null policy, and responsible-use boundaries. It does
not read SQLite or reconstruct targets/models. About / Methods / Sources is
still a separate shell and was not finalized in A7.7.

There is no map, deployment, live forecast, model fitting, or causal analysis. Overview
metrics, Explorer predictions, and Performance holdout diagnostics are
retrospective and do not establish generalization beyond the single temporal
holdout.

## Visual Conventions

Plotly charts share `dashboard.visual_style`: Arial-based typography, light
gridlines, responsive width, consistent hover surfaces, and hidden persistent
toolbars. Teal marks observed activity and logistic primary; blue marks
expected activity; orange marks HGB sensitivity and the final temporal
holdout; gray is a reference; purple marks gap status. Line style, marker,
pattern, and explicit text reinforce these meanings.
Evaluation populations are named Development OOF and Final temporal holdout.
Probabilities/prevalence use one decimal percent, startup rates two decimals,
employment growth one decimal percent, alignment percentage points, scores
three decimals, lift two decimals with ×, and counts use separators. The metric
glossary is centralized in `dashboard.glossary`.
