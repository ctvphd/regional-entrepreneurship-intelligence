# Assignment 6.1 Modeling Design

**Status:** Design frozen for review. This document specifies the method; it does not fit models, estimate expected entrepreneurship, compute residuals, or create labels.

## Research Question

Can historical industry growth, entrepreneurial activity, labor-market conditions, and regional economic characteristics predict whether entrepreneurial activity within an MSA-industry combination will fall below its expected level over the subsequent three years?

## Two-Stage Modeling Framework

1. Estimate a defensible expected startup rate conditional on information observed at or before the outcome-year observation.
2. Use predictors available at year `t` to predict whether the MSA-sector's residual at exactly `t+3` is below the training-derived threshold.

Expected entrepreneurship prioritizes construct validity, interpretability, temporal validity, stability, then predictive fit. Maximum R-squared is not the sole objective.

## Assignment 5 Evidence Informing the Design

The pooled employment-growth/startup association is positive but weak (Pearson 0.099; Spearman 0.193). All 19 sector correlations are positive but vary materially, and year/sector controls raised exploratory R-squared from 0.0098 to 0.342. Excluding 2020-2021 leaves the correlation positive; those years remain in the primary sample with year controls. Startup lag-1 correlation is 0.690 pooled but 0.077 within-panel demeaned. Growth is heavy-tailed; temporary tail trimming changed magnitude but not sign. Employment/payroll growth correlate 0.714 and income/education 0.613. The 19.29% A5 high-growth/low-startup quadrant is descriptive only and never defines or tunes the formal gap target.

## Expected Entrepreneurship Definition

Expected entrepreneurship is the startup rate predicted for an MSA-industry-year from information available at or before that year, conditional on industry growth, prior entrepreneurship, sector context, year context, and regional economic conditions.

The response is `startup_rate`. The primary expected-model candidate is a linear model with `startup_rate_lag1`, `employment_growth`, candidate regional controls, sector fixed effects, and year fixed effects. The formula is a candidate for A6.2, not an implemented model. Lag 2/3 and alternative growth measures are sensitivities. Do not automatically include correlated growth measures together.

A6.2 should compare a linear baseline, a sector-sensitive version adding `employment_growth × sector`, and only if diagnostics justify it, a robust or nonlinear sensitivity candidate. Random Forest/XGBoost are not the primary expected-entrepreneurship construct.

## Alignment Definition

`alignment_residual = observed_startup_rate - expected_startup_rate`

Positive means above expectation; near zero means approximately aligned; negative means below expectation. A negative residual alone is not a gap.

## Primary Gap Definition

The primary candidate is a residual at or below the **20th percentile of residuals in the relevant training fold**. This is the bottom quintile, not the A5 descriptive quadrant. A6.3 must also examine bottom 10%, bottom 25%, and residual below training residual mean minus one training residual standard deviation. The threshold is never re-estimated from validation/test residuals; apply each fold's training cutoff unchanged to its future observations. Future prevalence may differ from 20% and must not be normalized by year.

## Prediction Horizon

The primary horizon is exactly three calendar years: predictors at `t` map only to the same MSA-sector at `t+3`. Require the exact target year; a third subsequently observed row does not qualify. The panel ends in 2023, so the latest targetable predictor year is **2020**. The observed panel has 4,020 exact pairs for 2020→2023 and 43,921 exact t→t+3 pairs over 2010-2020. Pair counts are key-contiguous counts before feature-completeness filtering.

## Feature Time Boundary

Predictive feature matrix `X_t` may contain only values dated `t` or earlier. It must not contain t+1/t+2/t+3 startup, growth, ACS, residual, expected-rate, or target values. Target construction is a separate, fold-local operation: fit the expected-rate model using years available through the fold's training-outcome cutoff, then apply it to an eligible target-year row to calculate that row's expected rate and residual against its observed startup rate. Target-year covariates used internally by this fold-fitted benchmark are **label-construction inputs only**; they may not enter `X_t`. No full-sample expected model or residual cutoff is permitted.

## Temporal Validation

Primary validation is expanding-window temporal validation. Fold specifications, outcome cutoffs, and key-pair counts are in `docs/ASSIGNMENT6_TEMPORAL_FOLDS.md` and `config/assignment6_temporal_folds.csv`.

| Split | Training predictor years | Training target years / outcome cutoff | Validation predictor years → target years | Calendar-paired validation rows | Expected-model fit years |
|---|---|---|---|---:|---|
| Fold 1 | 2010-2013 | 2013-2016 / 2016 | 2014 → 2017 | 4,000 | 2010-2016 |
| Fold 2 | 2010-2014 | 2013-2017 / 2017 | 2015 → 2018 | 3,997 | 2010-2017 |
| Fold 3 | 2010-2015 | 2013-2018 / 2018 | 2016-2017 → 2019-2020 | 7,988 | 2010-2018 |
| Final holdout (untouched) | 2010-2017 | 2013-2020 / 2020 | 2018-2020 → 2021-2023 | 12,091 | 2010-2020 |

Training pair counts are 15,845, 19,845, 23,842, and 31,830 respectively. Training outcomes in every fold end before the first validation target year. Fold 1-3 support development/specification comparisons; the final 2018-2020 predictor block and 2021-2023 outcomes are not for model/specification/threshold selection. Do not evaluate the holdout in A6.1. During A6.2-A6.5, every first-stage fit, preprocessing step, residual threshold, and model-selection decision must respect each row's temporal cutoff.

## Final Holdout

Reserve predictor years **2018-2020**, with exact outcomes in 2021-2023, as the final untouched temporal holdout. The development training set may use labeled predictor years through 2017 (outcomes through 2020). Do not use the holdout for first-stage specification selection, feature selection, preprocessing fit, threshold tuning, or hyperparameter tuning. Evaluate it only after the model and evaluation protocol are frozen.

## Baselines

- **Baseline 0:** constant probability equal to the natural gap prevalence calculated from training-fold labels only.
- **Baseline 1:** transparent logistic regression limited to predictor-year `startup_rate`, `startup_rate_lag1`, `employment_growth`, sector effects, and temporally valid year/time information. Fit all preprocessing and estimation on training data only.

Advanced classifiers must improve meaningfully on both. No model is fit in A6.1.

## Evaluation Metrics

Primary: **PR-AUC / Average Precision**. Secondary: ROC-AUC, recall, precision, F1, balanced accuracy where useful, Brier score, and calibration diagnostics. Accuracy is not primary. False negatives receive somewhat greater substantive concern, so report recall alongside precision and do not maximize recall without its precision tradeoff. A6.1 sets no final operating probability threshold.

Improvement must be positive on PR-AUC, reasonably consistent across development folds, avoid severe precision/recall deterioration, be reasonably calibrated, and be substantively useful. It must persist on the untouched holdout. Do not set an arbitrary fixed percentage gain; A6.4 may quantify a decision rule after observing baseline variability.

## Class-Imbalance Policy

Preserve natural prevalence. Do not downsample, synthesize observations, or alter the threshold to obtain a balanced class. Class weights and decision-threshold adjustments may be considered later. SMOTE/oversampling is excluded from the primary design absent strong later justification.

## Sector Effects

Sector fixed effects are mandatory in the primary expected-entrepreneurship candidate. A6.2 compares sector effects only against sector effects plus `employment_growth × sector`; select by interpretability, stability, out-of-sample behavior, and residual diagnostics, not p-value search. All 19 sectors remain in scope.

## Year Effects

Year effects are mandatory in the primary expected-model candidate. Retain 2020-2021 in the main data and use temporal validation/year context. Excluding 2020 and 2020-2021 are later sensitivity analyses, not the primary sample and not causal COVID estimates.

## MSA Effects Policy

Do not include MSA fixed effects in the primary expected model because stable place differences are substantively relevant. MSA fixed effects are sensitivity-only. Unseen-MSA evaluation is a separate A6.6 generalization robustness analysis, not the primary validation design.

## Heavy-Tail Policy

Retain original production values in the primary analysis; do not winsorize, cap, trim, or delete primary observations. Later non-destructive sensitivities may include rank-based comparisons, temporary P01/P99 trimming, robust regression or robust uncertainty, and denominator diagnostics. Do not create a weighted growth index.

## Leakage Safeguards

The binding checklist is `docs/ASSIGNMENT6_LEAKAGE_CHECKLIST.md`. In brief: exact calendar pairs only; fold-local expected model and training residual cutoff; training-only preprocessing and feature selection; no future values in `X_t`; target-year benchmark inputs restricted to label construction; and the final holdout remains untouched until evaluation protocol freeze.

## Model-Acceptance Criteria

Expected-rate candidates require out-of-sample MAE/RMSE and R-squared where useful; residual mean, distribution, skewness, extremes, year/sector/MSA stability, remaining year/sector structure, and coefficient stability across temporal folds. Gap targets require training/validation prevalence overall and by year, sector, and MSA, plus threshold stability. Future prevalence is not forced to 20%.

## Assignment 6 Iterative Plan

1. **A6.1** Target Definition, Baseline & Temporal Validation Design (this step).
2. **A6.2** Expected Entrepreneurship Model.
3. **A6.3** Entrepreneurial Gap Target Construction.
4. **A6.4** Baseline Prediction Model.
5. **A6.5** Advanced Predictive Models.
6. **A6.6** Robustness, Interpretation & Generalization.
7. **A6.7** Final Analytics Engine, QA & Assignment 6 Completion.

Only A6.1 design and validation scaffolding are in scope now. Do not proceed to A6.2 until this specification is reviewed.
