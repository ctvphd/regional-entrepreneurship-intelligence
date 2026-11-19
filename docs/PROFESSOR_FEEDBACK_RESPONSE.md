# Professor Feedback Response

## Feedback Received

The clean-review gap was that production SQLite and local caches are not committed, while the dashboard data-layer build test expected the production database. A clean reviewer therefore could not reproduce the full empirical build from this repository alone.

## Changes Implemented

- Added a deterministic synthetic source set and a separate review database command using the existing A4 raw loaders, four source transformations, and analytics panel builder.
- Added a descriptive dashboard-panel Parquet artifact and loader integration test from the generated review database; it contains no synthetic model scores or performance metrics.
- Production preflight now reports total required/present/missing inputs and every missing path, and fails before database or log creation. It never falls back to synthetic inputs.
- Added reviewer quickstart, methodological boundaries, synthetic-source notes, and report. The existing frozen production estimates and model artifacts were not rebuilt or edited.

## Methodological Clarifications

### 1. Grain, mappings, and missingness

The analytical row is one MSA/CBSA x 2022 NAICS 2-digit sector x year, keyed by geography, industry, and year IDs. BDS uses 2017 sector coding and the existing documented sector concordance to the 2022 analytical reference; its MSA code is checked against the selected July 2023 CBSA reference. QCEW and CBP county records are aggregated through the county-to-CBSA crosswalk; ACS controls are MSA-year and left-joined. Suppression and missing values are not zero-filled. BDS suppressed/missing startup rows remain auditable in staging and do not enter the accepted core; QCEW/CBP aggregation requirements are applied by their existing transformations; missing ACS support does not drop a core row. The synthetic test demonstrates the same distinctions, but cannot measure production mapping coverage or suppression rates.

### 2. Gap definition

Observed startup rate is age-0 BDS firm startups divided by all BDS firms in the same MSA-sector-year. A fold-specific expected-startup benchmark produces the alignment residual (observed minus expected). The primary gap label is residual at/below that fold's training-residual 20th percentile. Expected values, residuals, and the cutoff are constructed inside folds; the outcome is a model-relative entrepreneurial response gap, not an administrative label or objective ecosystem deficit.

### 3. Timing and leakage

Predictors are dated `t`; the label is the same geography-sector at exact calendar year `t+3`. Feature availability is restricted to `t` or earlier, and lags use prior calendar years only. Target-year covariates used by the fold-fitted expected model are label-construction inputs, not classifier features. The cutoff is training-derived and is not globally normalized using future outcomes.

### 4. Study window

The proposal scoped 2005-2023. The realized validated primary period is 2010-2023 because that is the documented comparable source window. This omits early years while retaining the prespecified temporal holdout; it narrows historical coverage rather than changing target or panel definitions.

### 5. Baselines and evaluation

Logistic regression is primary; Average Precision is the primary ranking metric and is compared with the natural-prevalence/no-information ranking. ROC-AUC, Brier, lift, recall, precision, F1, and calibration are secondary. Class prevalence remains natural and the primary analysis does not use SMOTE. Robustness includes alternative models and gap definitions, geographic holdout, and MSA-size variation. Synthetic fixture values are not used to calculate or report these metrics.

### 6. Causal boundary

The evidence supports prediction and predictive association only. It does not identify a causal effect of industry growth on entrepreneurship. Wording should use “predicts,” “associated with,” or “predictive signal,” not “causes,” “leads to,” or “proves.”

### 7. What still requires production access

Without the authorized production cache, a reviewer cannot independently verify full production crosswalk coverage, suppression prevalence, exact final panel size, target prevalence, final predictive performance, or full temporal/geographic generalization. The synthetic fixture verifies the implemented transformation path, source schemas, mapping/join behavior, null/suppression rules, lags, key constraints, SQLite generation, and descriptive dashboard loading only.

## Production-Only Results

The 63,577-row production panel and final predictive metrics remain production-cache-derived and are not claimed as independently reproduced by this review fixture. Large source files and the production SQLite file remain outside Git.

## A6.8A Reviewer-Engine Remediation

The Assignment 6 runner now has an explicit `--source reviewer` path that rebuilds the fictional fixture and exercises temporal validation, exact `t+3` target construction, the expected-rate and gap-label helpers, registered predictor restrictions, and logistic execution. The reusable temporal window is explicit rather than inferred from whatever years happen to be present. Production defaults remain frozen at 2010-2017 development predictors, 2018-2020 holdout predictors, and a three-year horizon; production still fails closed when its authorized database or locked inputs are unavailable and never substitutes reviewer data.

Reviewer outputs are isolated under `data/review/assignment6/` and state that they are execution-path validation only. The reviewer configuration uses 2018-2019 development predictors and a 2020 synthetic holdout over the fixture's 2017-2023 span. Clean-clone tests now create temporary parent directories and build their own fixtures, so no test requires a pre-existing `data/review/` directory, reviewer database, manual fixture command, or favorable test order. This remediation does not claim independent reproduction of the production A6 results.

## A6.8B Holdout AP Uncertainty

The frozen 10,304-row holdout predictions were evaluated with 5,000 paired MSA-cluster bootstrap replications using seed 754; all replications contained both classes. Logistic AP remains 0.404225 with a 95% percentile CI of 0.380018-0.429251. HGB AP remains 0.424238 with a CI of 0.397723-0.449830. The paired HGB-minus-Logistic difference is 0.020014 with a CI of 0.005531-0.033684, and HGB exceeded Logistic in 99.72% of valid resamples.

The interval is above zero, so the holdout ranking difference is distinguishable from zero under this resampling design. The prespecified model-switch rule nevertheless is not met: although the observed gain just exceeds 0.02 and HGB is higher in all three holdout target years, HGB exceeded Logistic in only two of three development folds and its pooled development OOF gain was 0.004. Logistic remains the primary model; this post-assignment remediation did not refit models or alter labels, predictions, or evaluation rows.

## A7.8D Verification Addendum

- The synthetic reviewer build completed with seven source files, 27 analytical rows, two fictional MSAs, two sectors, 2017-2023 coverage, zero duplicate keys, four quality checks, and zero foreign-key violations. Repeatability, dashboard-loader integration, exact t+3 pairing/prior lags, and mocked missing-cache preflight passed in focused tests (3 tests in the current sandbox run).
- The production dashboard artifact health command passed; its descriptive panel has 63,577 rows and its coverage file has 381 MSAs. The Explorer AppTest passed in the prior project verification record; a current rerun stalled at initial rendering in this sandbox. Prior notes record a 196-test pass, but the full offline suite is not newly verified here.
- The clean reviewer path does not require the production SQLite database. Production empirical panel/metrics and reviewer-fixture output remain explicitly separate.
- The current machine inventory found 58 of 58 required production cache files. Because all inputs are present, a real missing-cache execution was not run; mocked testing verified exact path reporting and no DB/log creation when inputs are absent.
- Seven topics are addressed above: analytical grain/mapping/missingness; gap construction; timing/leakage; study window; baselines/evaluation; causal interpretation; and what requires production access.

## Current A7.10 Boundary

Read-only production verification confirmed 63,577 analytical rows and four retained failed run-metadata rows from two interrupted end-to-end invocations at BDS ingestion before panel integration. No production panel integration or model rebuild completed; this incident affected run metadata only. Full-suite completion and five-route browser QA remain unverified in this sandbox, as recorded in `reports/assignment7_final_integration.md`.
