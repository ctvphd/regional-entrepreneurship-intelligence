# Assignment 6.7 Final Model Lock

**Status:** Locked before final-holdout outcomes are loaded or evaluated.
**Lock commit:** recorded by Git history for this file; source HEAD at lock preparation was `bb9307d`.

## Frozen target construction

- Primary label: `gap_p20`, with an exact same-CBSA/same-2-digit-sector `t` to `t+3` pair.
- Expected-startup benchmark: A6.2 Model A, OLS formula `startup_rate ~ startup_rate_lag1 + employment_growth + acs_population_growth + median_household_income + educational_attainment_pct + labor_force_participation_pct + unemployment_rate + C(sector_code) + C(year)`.
- Final benchmark fit and residual-threshold population: complete Model A rows available through 2020; no 2021-2023 response or covariate rows may enter this fit.
- The p20 threshold is the empirical 20th percentile of Model A's in-sample development residuals through 2020, equality inclusive. Frozen numerical development p20 cutoff: `-1.4783450423889537` startup-rate points, calculated from 38,061 in-sample development residuals with linear interpolation. It was computed by a query bounded at year 2020, before any holdout target-year query or scoring.
- For target years beyond 2020, year fixed-effect input is capped at the latest fitted year, 2020, following the documented A6.2 carry-forward rule. Other target-year benchmark covariates are used only to construct the label, never as predictive features.

## Frozen predictive models

### Primary reference: simple logistic

- Model: A6.4 `baseline_1_simple`, using the existing ridge-stabilized binomial GLM implementation (`statsmodels.GLM`, binomial family, L2 regularization `alpha=1e-5`, `L1_wt=0`, `maxiter=500`).
- Predictors: `startup_rate`, `startup_rate_lag1`, `employment_growth`, categorical `sector_code`, and standardized linear `year` trend. No ACS controls and no MSA fixed effects.
- Numeric scaling: training-sample means and population standard deviations (`ddof=0`); sector levels and reference contrast learned from training only; unseen sector levels receive zero contrasts. The year trend is standardized by the training sample in the same manner.
- Training population: unique exact development pairs with predictor years 2010-2017 and targets through 2020; label-construction eligibility as above; common A6.4 complete-case rule (`baseline_2_extended` required fields) for consistent paired-comparison eligibility. ACS variables determine sample completeness only and are not predictors in this model.

### Nonlinear sensitivity: HistGradientBoosting

- A6.5 model: `hist_gradient_boosting`, trained on the same eligible development/holdout rows with its frozen A6.5 extended feature family (`startup_rate`, `startup_rate_lag1`, `employment_growth`, five ACS controls, `sector_code`, `year`).
- Frozen configuration, development winner candidate 1 in all three folds: `max_iter=120`, `learning_rate=0.05`, `max_leaf_nodes=15`, `min_samples_leaf=30`, `l2_regularization=1.0`, `early_stopping=False`, `random_state=20261004`.
- No candidate search, retuning, or feature changes are permitted on holdout data.

## Evaluation protocol

- Holdout predictors: 2018-2020; exact target years: 2021-2023. Primary metric: Average Precision (PR-AUC). Secondary metrics: ROC-AUC, Brier, recall, precision, F1, balanced accuracy, calibration, and lift.
- Thresholded classification is diagnostic only. Primary diagnostic policy is the natural positive prevalence of the final development training labels, consistent with A6.4/A6.5 fold-training-prevalence reporting. The A6.4 fixed `0.50` diagnostic is also reported. Neither threshold is optimized using holdout labels.
- Calibration bins, lift cut points (top 10%, 20%, 25%), yearly/sector/MSA-size summaries, and metric comparisons are prespecified diagnostics. None may be used to change model, features, threshold, or data eligibility.
- Holdout labels and outcomes may be joined only after this lock is committed. No holdout-derived value may flow into fitting, preprocessing, target cutoffs, tuning, or model choice.

This file and its Git commit establish the decision record preceding final-holdout evaluation. A6.7 is evaluation and reporting only; no Assignment 7/dashboard work is authorized here.
