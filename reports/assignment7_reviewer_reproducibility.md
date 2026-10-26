# Assignment 7 Reviewer Reproducibility

## Executive Summary

A clean clone can now build a small synthetic review database by running the existing A4 ingestion and transformation code. The reviewer path is isolated from production, creates no model-performance claims, and emits a dashboard-loader-compatible descriptive panel.

## Professor Feedback and Reproducibility Gap

The production SQLite database and source caches are local/ignored. The original dashboard data-layer integration expected that database, so a clean reviewer could not execute that path. Production empirical outputs remain reproducible only with the authorized local source cache. The production runner now reports full cache preflight detail and stops before writing if inputs are absent.

## Synthetic Fixture Design and End-to-End Path

`tests/fixtures/reviewer_sources/` holds seven small deterministic files: BDS backbone, BDS firm-age, QCEW county-sector, ACS metro controls, CBP county-sector, synthetic county-to-CBSA mapping, and synthetic NAICS mapping. Fictional geographies are 99901/99902; sectors are 11/54; the source records use years 2010-2023 for BDS and 2017-2023 for the integrated core. One BDS row is suppressed, another has a true zero age-0 count, one ACS estimate is blank, and an unmatched geography/industry is explicit.

The build path is synthetic CSVs -> existing raw loaders -> existing BDS/QCEW/ACS/CBP transformations -> existing analytics panel builder -> separate `data/review/reviewer_fixture.sqlite` -> dashboard-compatible descriptive Parquet -> dashboard allow-listed loader. No production SQLite is opened or written.

## Grain, Crosswalks, and Missingness

The analytic grain remains geography x 2-digit 2022 NAICS sector x year. The fixture yields **27 rows**, 2 synthetic MSAs, 2 sectors, years 2017-2023, zero duplicate keys, and zero foreign-key violations. One otherwise eligible BDS record is excluded because the startup numerator is suppressed. True zero remains zero; blank ACS support stays null; unmatched codes do not enter the analytical core. The fixture only demonstrates those rules; it does not estimate their production frequency.

## Gap Construction and Leakage Controls

The A6 gap is a model-relative entrepreneurial response gap. The observed rate is age-0 BDS firm startups divided by all BDS firms. Expected rate/residual and the p20 cutoff are fold-local; classifier predictors use `t` or earlier and the outcome is at exact `t+3`. Target-year expected-model inputs are confined to label construction. Existing A6 tests exercise training-only cutoffs and exact pair requirements. Synthetic values do not validate gap prevalence or performance.

## Study Window, Baselines, and Causal Boundaries

Proposal scope: 2005-2023. Validated primary scope: 2010-2023 because of source availability/comparability; early coverage is narrower while the temporal holdout is retained. Logistic regression and Average Precision are primary, with natural-prevalence ranking as the benchmark. ROC-AUC, Brier, lift, recall, precision, F1, and calibration are secondary. Class balance is natural; no SMOTE is used in primary analysis. Robustness includes alternate models/definitions, geography holdout, and MSA-size variation. Findings are predictive/associational, not causal.

## Production-Only Results and Remaining Limitations

Production panel size (63,577), production coverage/suppression, target prevalence, final model metrics, and complete production repeatability remain cache-dependent. A reviewer without that cache cannot independently assess those results. The fixture does not simulate production row counts or estimate predictive metrics.

## Production Preflight

The current local machine has 58/58 required production cache paths present. The real absent-cache CLI preflight was therefore not invoked because it would pass preflight and start production ETL. The mocked preflight test verifies missing totals, exact path reporting, and no database/log creation when inputs are absent. During verification, two production CLI invocations were mistakenly started before the cache inventory was confirmed, then interrupted during BDS ingestion before panel integration. Their four run-metadata rows were marked `failed` with an interruption note. A read-only audit afterwards confirmed 63,577 analytics rows, 246,050 raw/staging BDS rows, and 178,382 BDS intermediate rows. No production panel, target, model, or metric build ran to completion.

## Clean-Environment and Repeatability Results

The fixture command ran twice successfully and each run reported 7 source files, 27 rows, 2 MSAs, 2 sectors, 2017-2023, zero duplicate keys, zero FK violations, and four passing quality checks. The dashboard Parquet SHA-256 was identical across runs (`288D0D272031C1D860C57E28B341F7469529648EF573A8ED143445A5996E5873`). The full suite and an isolated rerun reached `test_explorer_renders_without_exceptions_and_keeps_categories_unavailable` and stalled in this headless environment; focused reviewer/preflight tests pass. A destructive removal of the local production database was not used to simulate a clean clone; the reviewer build itself ran against its separate review-database path.

## Dashboard Integration

The test loads the generated descriptive panel through the dashboard allow-listed loader using the review output directory. Full A7.2 model and performance artifacts are deliberately not synthesized. The production A5/A6 reconciliation test class is skipped with an explicit reason if the canonical production SQLite file is absent. Independent end-to-end review integration is covered from the synthetic database and review Parquet.

## Readiness

A7.8D is limited to reviewer reproducibility. A7.9 is deferred as optional deployment work. A7.10 documentation and read-only checks are recorded, but the full offline suite and five-route browser smoke QA remain unverified in the current sandbox; see `reports/assignment7_final_integration.md`. No map, deployment, or production model run is included.
