# Assignment 7 Final Integration, QA & Completion

## Executive Summary

A7.10 documentation reconciliation and read-only data checks are complete. The synthetic reviewer fixture builds 27 rows from seven fictional source files; its repeatability, three-year pairing, dashboard-loader, and mocked production-preflight tests pass. Production dashboard artifacts pass the health check, and the production analytical table remains at 63,577 rows. This closeout is **partial**: the full offline suite stalls in the Explorer Streamlit AppTest in this sandbox, and a browser could not connect to a locally launched Streamlit server, so five-route visual QA is not confirmed here.

## Final Project State and Assignment Alignment

Assignments 3-7 form a coherent progression from research proposal, through the A4 database/ETL and A5 exploratory analysis, to A6 expected entrepreneurship and leakage-aware prediction, then A7 dashboard communication and synthetic reviewer reproducibility. The proposal's 2005-2023 scope became a validated 2010-2023 primary window because of source compatibility and feasibility; this is a documented scope refinement. See [A3-A7 alignment](../docs/PROJECT_ALIGNMENT_A3_A7.md).

## Research Design and Final Metrics

The unit is July 2023 CBSA/MSA x 2-digit 2022 NAICS x year. Startup rate is the entrepreneurship measure; employment growth is the primary opportunity measure. Year-t predictors map to the exact same metro-sector at t+3. Logistic Regression is the preselected primary model; HistGradientBoosting is a sensitivity model. The final holdout covers target years 2021-2023.

| Sample | Model | N | Prevalence | AP | ROC-AUC | Brier | Recall | Precision | F1 | Top-decile lift |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Development OOF | Logistic Regression | 13,633 | 19.1% | 0.367 | 0.693 | 0.142 | - | - | - | - |
| Final temporal holdout | Logistic Regression (primary) | 10,304 | 23.3% | 0.404 | 0.692 | 0.164 | 0.708 | 0.328 | 0.448 | 1.99x |
| Final temporal holdout | HistGradientBoosting (sensitivity) | 10,304 | 23.3% | 0.424 | 0.708 | 0.161 | - | - | - | 2.09x |

The outcome is a fold-local model-relative negative deviation below the development-derived p20 residual threshold, not an administrative outcome, causal ecosystem failure, or normative ideal. Classifier predictors use year t or earlier; target-year benchmark inputs only construct the label; the final holdout was not used for model selection.

## Dashboard and Provenance

The production A7.2 artifact health check passed: panel 63,577 rows, predictions 23,937, coverage 381, and all required datasets/metadata/filters valid. Frozen dashboard values trace to A7.2 artifacts and finalized A6 outputs; synthetic review outputs are isolated under `data/review/`.

Browser route review of Overview, Explore Markets, Model Insights, Data & Confidence, and About the Analysis was attempted but not verified: localhost returned connection refused, and the Streamlit launch did not expose a listener in this execution environment. The Explorer AppTest also stalled at initial rendering during the full suite. No route is claimed visually verified by this A7.10 run.

## Reviewer Reproducibility and Production State

`uv run python -m regional_entrepreneurship_intelligence.review.build_reviewer_fixture` succeeded: 7 source files, 27 rows, 2 fictional MSAs, 2 sectors, 2017-2023, no duplicate keys, four quality checks, and zero foreign-key violations. The review Parquet loads through the dashboard loader. Focused reviewer and mocked-preflight tests passed (3 tests).

The read-only production query confirmed 63,577 analytical rows. The four latest metadata records are failed runs dated October 25, 2026, marked as interrupted during BDS ingestion before panel integration; no successful production run was invoked during this A7.10 work. The production database file timestamp and frozen model artifact values were not rewritten by the reviewer fixture. This local machine has 58/58 required production cache inputs. Production metrics and empirical results still require that authorized cache for independent rebuilding.

The production cache incident affected run metadata only: two end-to-end invocations and two BDS-stage records were interrupted, four rows were marked failed, and no panel integration or production model rebuild completed. The retained panel count and frozen A6/A7 artifacts are unchanged.

## Professor Feedback and Reproducibility Boundary

The response covers seven topics: unit/mappings/missingness; gap definition; timing/leakage; period; baseline and evaluation; causal boundary; and production-only evidence. The clean-clone path tests source-shaped synthetic ingestion, transformations, schema/key/FK behavior, target timing/lag contracts, and descriptive dashboard loading. It does not reproduce production crosswalk or suppression prevalence, empirical target prevalence, final model results, or generalization evidence.

## Testing and Integrity

- Starting baseline: the project records 196 passing tests in the prior A7.8D verification supplied with the task; that historical result was not reproduced in this sandbox.
- Current focused reviewer/preflight tests: 3 passed in 9.199 seconds.
- Current full-suite attempt: did not complete; it stalled at `test_explorer_renders_without_exceptions_and_keeps_categories_unavailable` during initial Streamlit rendering. Initial temp-directory errors were resolved by setting `TEMP`/`TMP` to a writable repo scratch directory.
- Dashboard artifact health: passed all checks.
- `uv lock --check`: passed. `git diff --check`: passed (Git emitted only expected LF-to-CRLF working-copy notices).
- Production database: read-only panel count 63,577; no production rebuild performed.

## Limitations, Practical Use, and Optional Work

The primary limitations are model-relative outcome, narrow startup-rate construct, two-digit sector aggregation, complete-case selection, uneven metro support, unmodeled geographic dependence, one temporal holdout, imperfect calibration, and production-cache dependence. Appropriate use is screening for further investigation, not causal diagnosis, policy automation, funding allocation, live forecasting, or guaranteed outcomes. The only remaining optional work is deployment/containerization, a geographic map, publication-quality figures, and dissertation extensions; none was started.

## Remaining Blockers

Mark A7.10 complete only after the offline test suite exits successfully and the five dashboard routes can be smoke-tested in a browser or equivalent supported app test. Until then, the deliverables and data integrity checks are reconciled, but final integration QA remains partial.
