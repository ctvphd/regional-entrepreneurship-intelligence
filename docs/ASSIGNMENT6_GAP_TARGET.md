# Assignment 6.3 Entrepreneurial-Gap Target Specification

**Status:** Constructed for development folds only. No classifier or final-holdout target labels were created.

## Mathematical definition

For an MSA `i`, sector `s`, and outcome year `y`, the selected expected-startup-rate benchmark is A6.2 Model A, refitted within the current temporal fold:

`expected_startup_rate[i,s,y] = f_A(startup_rate_lag1, employment_growth, ACS controls, sector FE, year FE)`

`alignment_residual[i,s,y] = observed_startup_rate[i,s,y] - expected_startup_rate[i,s,y]`

For fold `k`, let `c20[k]` be the empirical 20th percentile of finite in-sample residuals from complete-case Model A training rows only. The primary target is `gap_p20 = 1(alignment_residual <= c20[k])`; equality is included. A negative residual alone is not a gap. The p20 cutoff is estimated once per fold, never pooled across folds, and is applied unchanged to that fold's training target pairs and validation target pairs. Training-pair prevalence can differ slightly from 20% because target pairs are a subset of the complete-case residual sample and ties at the cutoff are included.

## Selected benchmark and sensitivity cutoffs

Model A is OLS with lag-1 startup rate, employment growth, five ACS regional controls, sector fixed effects, and year fixed effects. Complete cases only; no imputation. For an unseen validation year, A6.2's documented rule carries forward the latest fitted training-year effect.

| Fold | Training residual N | p10 | Primary p20 | p25 | Mean minus 1 SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| fold_1 | 22450 | -2.3541 | -1.4699 | -1.1638 | -2.3585 |
| fold_2 | 26337 | -2.3451 | -1.4672 | -1.1614 | -2.3339 |
| fold_3 | 30230 | -2.3531 | -1.4762 | -1.1629 | -2.3426 |

The p10, p25, and training residual mean minus one sample standard deviation cutoffs are diagnostic robustness rules only. They do not replace p20. The residual margin is `gap_margin = alignment_residual - c20[k]`; negative values are at/below the cutoff, zero is on it, and positive values are above it.

## Exact target-pair logic and separation

Only same-CBSA, same-sector rows with `target_year = predictor_year + 3` are eligible. A missing exact target is excluded; no nearest-year or third-available-row substitution is used. The pair artifact contains identifiers, years, target-year observed/expected startup rate, residual, fold cutoff, margin, labels, and split role. It does not include any predictor-year feature matrix. Target-year covariates used by Model A are confined to target construction and may not enter `X_t` in A6.4.

Both fold training and validation pair labels are written for development-only diagnostics. Training thresholds use the entire fold-specific complete-case first-stage training residual sample; they do not use validation residuals. The validation intervals are target years 2017, 2018, and 2019-2020 according to A6.1. The final holdout target years 2021-2023 are not read into target construction or diagnostics and do not appear in the artifacts.

## Class balance and prohibited changes

Natural prevalence is retained. No downsampling, SMOTE, class weighting, or threshold adjustment is performed. The primary label is the binary outcome for later prediction; gap margin, prevalence groups, transitions, and severity-like diagnostics are not substitutes for it. A5's high-growth/low-startup median quadrant is compared for face validity only and never defines the formal gap.

No future target-year variable, expected rate, residual, or label may appear in predictor-year `X_t`. Do not train a classifier, tune predictive decision thresholds, or inspect final-holdout target performance in A6.3.
