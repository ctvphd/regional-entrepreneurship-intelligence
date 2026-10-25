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
