# Assignment 6.7 Analytics Engine

## Purpose and Frozen Design

This stage evaluates the final locked A6 design on the reserved temporal holdout. It does not select a new model. The primary reference is the A6.4 simple logistic model; the frozen A6.5 HistGradientBoosting model is a sensitivity. The exact specification and development-only residual threshold are recorded in `ASSIGNMENT6_FINAL_MODEL_LOCK.md`.

The outcome is an MSA-sector startup-rate gap relative to the A6.2 expected-startup benchmark, three years after predictor time. The primary metric is Average Precision (AP), interpreted against natural holdout prevalence. ROC-AUC, Brier score, classification diagnostics, calibration, lift, and descriptive subgroup/year metrics provide context. There are no causal claims.

## Temporal Boundary

Development target outcomes end in 2020; development classifier predictors end in 2017. The final holdout pairs predictor years 2018–2020 with exact target years 2021–2023. Pairing requires the same CBSA and sector at `t` and `t+3`. The first-stage Model A fit and numeric p20 residual threshold are development-only. Target-year benchmark covariates may construct labels but never enter the predictor matrix. SQLite access is read-only.

Both classifiers use the locked A6.4 common complete-case eligibility rule. The primary logistic uses only startup rate, its lag, employment growth, sector contrasts, and standardized linear year trend; ACS fields determine common sample eligibility but are not logistic predictors. The sensitivity HGB uses the frozen extended feature family and frozen hyperparameters. Thresholds are diagnostics only: development-label prevalence is primary, with fixed 0.50 separately reported. Neither is chosen from holdout performance.

## Run and Outputs

From the repository root, run:

```powershell
uv run python -m regional_entrepreneurship_intelligence.models.run_assignment6
```

The runner fails closed if the lock is uncommitted/changed, the threshold record is absent or inconsistent, or the frozen design does not match. It prints SHA-256 hashes for generated tables. Main deliverables are `reports/assignment6_final_analytics_engine.md`, `reports/tables/a6_final_*.csv`, and `reports/figures/a6_final_*.png`.

The tables include model performance, row-level holdout predictions, calibration deciles, yearly/sector/MSA-size summaries, research-question mapping, sample-flow audit, size cutpoints, and fixed-0.50 diagnostics. Sector AP/ROC-AUC are suppressed where positive events are fewer than 30 or no negative class is available.

## Final Holdout Summary

There are 10,304 eligible holdout rows from 365 MSAs and 19 sectors; the gap prevalence is 23.3%. The locked logistic achieved AP 0.404 (1.74 times prevalence), ROC-AUC 0.692, Brier 0.164, and top-decile lift 1.99. HGB achieved AP 0.424, ROC-AUC 0.708, Brier 0.161, and top-decile lift 2.09. The small HGB advantage is reported as a sensitivity result, not a reason to replace the interpretable primary reference.

Logistic holdout Brier is 0.022 higher than development OOF Brier. Calibration deciles show a useful monotone risk gradient but lower-decile overprediction and upper-decile underprediction at the extreme. Performance also varies across calendar years, sectors, and MSA-size groups. Complete-case selection is patterned, and 14.8% of exact holdout candidate pairs are excluded from the final comparison. These findings constrain use to historical prioritization among eligible observations and motivate external validation.

## Reproducibility and Interpretation

The committed lock and cutoff precede holdout scoring. Repeat runs must reproduce the table hashes; generated outputs must not alter the source SQLite database. Metrics describe predictive association only, not intervention effects. This is the final A6 evaluation stage; it does not authorize Assignment 7 or dashboard work.
