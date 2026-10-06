# Assignment 7.2 Dashboard Data Layer

## Executive Summary

A7.2 produces a typed, local Parquet layer from the read-only A4 analytical view and finalized A5/A6 artifacts. No model was fit, no target/threshold was changed, and holdout outcomes remain retrospective.

## Purpose

Provide deterministic datasets and pure-Python loaders for the future Streamlit app without repeatedly scanning the full analytical database. No UI, Plotly chart, map, or deployment code is included.

## Source Inventory and Lineage

The read-only `v_analytics_msa_industry_year` supplies descriptive values and quality flags. A6 fold-validation rows supply historical expected rates/residuals/p20 labels only through 2020. Separate A6 baseline/advanced OOF and final holdout artifacts supply frozen scores. A5/A6 audits supply coverage. Full field-level lineage is in `reports/tables/a7_dashboard_lineage_audit.csv` and `docs/ASSIGNMENT7_SOURCE_LINEAGE.md`.

## Dashboard Dataset Inventory

| Dataset | Rows | Columns | Primary key | Size (bytes) | Pages | Model output | Holdout outcome |
| --- | ---: | ---: | --- | ---: | --- | --- | --- |
| `dashboard_msa_industry_year` | 63577 | 40 | `cbsa_code+sector_code+year` | 3071427 | Executive Overview; Regional & Industry Explorer; Data Quality & Limitations | False | False |
| `dashboard_model_predictions` | 23937 | 13 | `cbsa_code+sector_code+predictor_year+target_year` | 491084 | Executive Overview; Regional & Industry Explorer; Data Quality & Limitations | True | True |
| `dashboard_model_summary` | 66 | 11 | `dataset_split+model+metric` | 8083 | Executive Overview; Model Performance | True | True |
| `dashboard_calibration` | 52 | 6 | `dataset_split+model+risk_bin` | 5323 | Executive Overview; Model Performance | True | True |
| `dashboard_model_by_year` | 6 | 9 | `predictor_year+target_year+model` | 5987 | Executive Overview; Model Performance | True | True |
| `dashboard_model_by_sector` | 38 | 10 | `sector_code+model` | 7811 | Executive Overview; Model Performance | True | True |
| `dashboard_model_by_msa_size` | 6 | 10 | `msa_size_group+model` | 6594 | Executive Overview; Model Performance | True | True |
| `dashboard_coverage` | 381 | 12 | `cbsa_code` | 16327 | Executive Overview; Regional & Industry Explorer; Data Quality & Limitations | False | False |
| `dashboard_sources` | 7 | 9 | `source_name+dataset` | 8071 | About / Methods / Sources | False | False |

## Historical vs Predictive Semantics

`dashboard_msa_industry_year.year` is a descriptive year. Its expected rate, alignment, and observed historical gap are populated only on A6 fold-validation target-year rows. `dashboard_model_predictions` is a separate pair-grain table with predictor year t and target year t+3; `actual_gap` is the later realized outcome. Development OOF and final holdout are explicit and never merged into a generic current score feed.

## Coverage Policy

A5 status uses its exact screen: >=100 rows, >=5 sectors, >=10 years. It maps to `comparison_eligible` or `thin`, is not a model reliability rating, and is validated against A5/A6 and analytical panel counts. A6 `model_eligible_flag` independently indicates any development OOF record.

## Null Policy

Source missingness/suppression and expected lack of historical A6 labels are preserved as Parquet nulls; no zero fill or UI imputation occurs. Holdout `fold` is null by design. Sector AP/ROC-AUC nulls retain A6 suppression below its event/no-negative-class rule. See `docs/ASSIGNMENT7_NULL_POLICY.md` and the generated field-level `docs/ASSIGNMENT7_DATA_DICTIONARY.md`.

## Model Result Preservation

Logistic is primary; HGB is sensitivity. Predictions, labels, cutoffs, and metrics are copied/reshaped from frozen A6 artifacts. The model summary reconciles from `a6_final_model_performance.csv`. No risk category is included because no non-holdout rule was frozen.

## Quality Checks

43 automated quality checks passed. Detailed names/results are in `reports/tables/a7_dashboard_quality_checks.csv`; the field-level audit is in `reports/tables/a7_dashboard_lineage_audit.csv`.

## Filter Readiness

`dashboard_filter_options.json` supplies CBSA/name, sector/name, descriptive years, observed historical binary gap values, and prediction availability/year options. It deliberately supplies no risk-category options. Model-performance metrics do not consume Explorer filters.

## Reproducibility and Database Integrity

Build with `uv run --offline python -m regional_entrepreneurship_intelligence.dashboard.run_data_layer`. Parquet uses PyArrow/Zstandard and stable table sorting; JSON is key-sorted, and metadata omits a volatile timestamp. All canonical database connections are read-only and query-only. Repeat-build output hashes are verified as a separate final QA step.

## Readiness for A7.3

The loader provides uncached pure-Python read functions and the contract preserves the A7.1 page/filter/model rules. A7.3 may build the Streamlit shell only after reviewing these schemas and the null/time-role rules. This report does not begin A7.3.
