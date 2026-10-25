# Reviewer Reproducibility

## Two Separate Paths

**Production reproduction** runs `uv run python -m regional_entrepreneurship_intelligence.etl.run_pipeline` and requires the authorized local production source cache. It never substitutes test data. The default production database is `database/assignment4_production.sqlite`.

**Clean-review reproduction** runs `uv run python -m regional_entrepreneurship_intelligence.review.build_reviewer_fixture`. It creates deterministic fictional source-shaped files, executes the existing A4 raw loaders, transformations, and analytics panel builder, and writes only to `data/review/`. This is not a production mode.

## What the Synthetic Path Verifies

The fixture exercises source ingestion, the July 2023 CBSA-shaped geography mapping, 2022 NAICS 2-digit sector references, source joins, suppression/null/zero distinctions, lag generation, analytical key uniqueness, SQLite foreign keys, a descriptive dashboard-compatible Parquet panel, and loading that panel with the dashboard loader. The key grain remains CBSA/MSA x 2-digit NAICS sector x year.

It does **not** establish production row counts, crosswalk coverage, suppression prevalence, target prevalence, predictive performance, generalization, or real-world estimates. No synthetic model metrics are produced.

## Production-Only Evidence

The 63,577-row production panel, production coverage and suppression summaries, target prevalence, final predictive metrics, and two-run production comparison require the authorized production cache. They are production-cache-derived results, not reproduced by the synthetic fixture.

## Methodological Boundaries

The proposal window was 2005-2023; the realized validated primary window is 2010-2023 because that is the source-compatible/comparable panel documented for the study. The narrower window reduces early-period coverage but retains the temporal holdout.

The A6 outcome is a **model-relative entrepreneurial response gap**, not a directly observed administrative label or objective ecosystem deficit. The observed startup-rate numerator is firm-age-0 BDS firms; the denominator is all BDS firms in the same MSA-sector-year. Expected startup rate and residual are constructed fold-locally; the primary cutoff is the training-fold residual 20th percentile. The target pairs predictor year `t` to the exact same CBSA-sector at `t+3`. Target-year benchmark inputs are label-construction inputs only, never classifier predictors. No global future-year normalization is used.

Logistic regression is the primary predictive model; Average Precision is primary and interpreted against natural prevalence/no-information ranking. Natural class balance is preserved; the primary analysis does not use SMOTE. ROC-AUC, Brier, lift, recall, precision, F1, and calibration are secondary diagnostics. Robustness work includes alternative models/target definitions, geographic holdout, and MSA-size variation. The study supports prediction and predictive association, not a causal effect of industry growth on entrepreneurship. Use “predicts,” “associated with,” and “predictive signal”; do not claim “causes,” “leads to,” or “proves.”

Without the production cache, a reviewer cannot independently audit full production crosswalk coverage, suppression prevalence, exact final panel size, target prevalence, final model performance, or full temporal/geographic generalization. The fixture verifies transformation behavior and integration contracts only.
