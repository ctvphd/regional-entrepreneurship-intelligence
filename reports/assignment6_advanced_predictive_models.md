# Assignment 6.5: Advanced Predictive Models

## Scope and safeguards

Random Forest and HistGradientBoosting are compared with the locked A6.4 simple logistic model on the exact same 52,124 complete-case development population and 13,633 outer-validation OOF keys. The final holdout was not loaded: predictors are queried only through 2017, OOF targets are limited to 2020, and validation results are diagnostic. No A6.6 geographic holdout or sensitivity analysis was performed.

All models predict the unchanged binary `gap_p20` outcome at exact t+3. The frozen A6.3 temporal folds and Baseline 2 complete-case filter are retained. Predictors are the A6.4 extended set: current and lagged startup rate, employment growth, five ACS controls, sector, and predictor year. Preprocessing is fitted within each training split. Class weights, resampling, and threshold optimization are not used.

Each outer fold has a small four-candidate grid search using only the latest predictor-year slice of that fold's training rows as a forward inner validation; candidate selection uses average precision (AP). The winning configuration is refit on the entire outer training fold. Outer validation AP is used only for reporting and permutation diagnostics, never for tuning.

## OOF performance

The baseline probability column is the locked A6.4 Baseline 1 prediction joined by full fold, geography, sector, predictor-year, and target-year keys. AP is primary; ROC-AUC and Brier are secondary. Recall, precision, and F1 use each outer fold's natural training prevalence as a descriptive threshold, not a selected operating rule.

| model | fold | validation_n | validation_prevalence | pr_auc | roc_auc | brier_score | recall | precision | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_1_simple | fold_1 | 3387 | 0.200 | 0.403 | 0.709 | 0.144 | 0.622 | 0.318 | 0.421 |
| random_forest | fold_1 | 3387 | 0.200 | 0.384 | 0.707 | 0.146 | 0.737 | 0.298 | 0.424 |
| hist_gradient_boosting | fold_1 | 3387 | 0.200 | 0.386 | 0.716 | 0.144 | 0.696 | 0.316 | 0.434 |
| baseline_1_simple | fold_2 | 3409 | 0.214 | 0.387 | 0.680 | 0.156 | 0.569 | 0.320 | 0.410 |
| random_forest | fold_2 | 3409 | 0.214 | 0.400 | 0.706 | 0.153 | 0.760 | 0.310 | 0.441 |
| hist_gradient_boosting | fold_2 | 3409 | 0.214 | 0.403 | 0.710 | 0.152 | 0.695 | 0.318 | 0.436 |
| baseline_1_simple | fold_3 | 6837 | 0.176 | 0.345 | 0.698 | 0.133 | 0.672 | 0.265 | 0.380 |
| random_forest | fold_3 | 6837 | 0.176 | 0.345 | 0.701 | 0.134 | 0.816 | 0.247 | 0.379 |
| hist_gradient_boosting | fold_3 | 6837 | 0.176 | 0.353 | 0.713 | 0.132 | 0.738 | 0.264 | 0.389 |
| baseline_1_simple | pooled_oof | 13633 | 0.191 | 0.367 | 0.693 | 0.142 | 0.630 | 0.290 | 0.397 |
| random_forest | pooled_oof | 13633 | 0.191 | 0.364 | 0.700 | 0.142 | 0.760 | 0.277 | 0.406 |
| hist_gradient_boosting | pooled_oof | 13633 | 0.191 | 0.371 | 0.711 | 0.140 | 0.699 | 0.294 | 0.414 |

Selected advanced model: **hist_gradient_boosting**. Its pooled OOF AP difference versus the locked simple logistic model is **+0.004**, and it exceeds logistic AP in 2 of 3 folds. Selection is conservative: the nonlinear model is treated as a diagnostic challenger, not a replacement absent a clear, consistent advantage.

## Inner tuning

| model | fold | candidate_id | inner_ap | inner_fit_n | inner_validation_n | inner_predictor_cutoff | inner_fit_target_max | inner_validation_target_min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_forest | fold_1 | 2 | 0.373 | 6297 | 3139 | 2013 | 2015 | 2016 |
| random_forest | fold_1 | 1 | 0.369 | 6297 | 3139 | 2013 | 2015 | 2016 |
| random_forest | fold_1 | 3 | 0.341 | 6297 | 3139 | 2013 | 2015 | 2016 |
| random_forest | fold_1 | 4 | 0.340 | 6297 | 3139 | 2013 | 2015 | 2016 |
| hist_gradient_boosting | fold_1 | 1 | 0.379 | 6297 | 3139 | 2013 | 2015 | 2016 |
| hist_gradient_boosting | fold_1 | 4 | 0.367 | 6297 | 3139 | 2013 | 2015 | 2016 |
| hist_gradient_boosting | fold_1 | 2 | 0.366 | 6297 | 3139 | 2013 | 2015 | 2016 |
| hist_gradient_boosting | fold_1 | 3 | 0.363 | 6297 | 3139 | 2013 | 2015 | 2016 |
| random_forest | fold_2 | 2 | 0.363 | 9436 | 3387 | 2014 | 2016 | 2017 |
| random_forest | fold_2 | 1 | 0.360 | 9436 | 3387 | 2014 | 2016 | 2017 |
| random_forest | fold_2 | 4 | 0.342 | 9436 | 3387 | 2014 | 2016 | 2017 |
| random_forest | fold_2 | 3 | 0.342 | 9436 | 3387 | 2014 | 2016 | 2017 |
| hist_gradient_boosting | fold_2 | 1 | 0.363 | 9436 | 3387 | 2014 | 2016 | 2017 |
| hist_gradient_boosting | fold_2 | 3 | 0.354 | 9436 | 3387 | 2014 | 2016 | 2017 |
| hist_gradient_boosting | fold_2 | 2 | 0.352 | 9436 | 3387 | 2014 | 2016 | 2017 |
| hist_gradient_boosting | fold_2 | 4 | 0.349 | 9436 | 3387 | 2014 | 2016 | 2017 |
| random_forest | fold_3 | 2 | 0.392 | 12823 | 3409 | 2015 | 2017 | 2018 |
| random_forest | fold_3 | 1 | 0.389 | 12823 | 3409 | 2015 | 2017 | 2018 |
| random_forest | fold_3 | 4 | 0.380 | 12823 | 3409 | 2015 | 2017 | 2018 |
| random_forest | fold_3 | 3 | 0.376 | 12823 | 3409 | 2015 | 2017 | 2018 |
| hist_gradient_boosting | fold_3 | 1 | 0.400 | 12823 | 3409 | 2015 | 2017 | 2018 |
| hist_gradient_boosting | fold_3 | 4 | 0.385 | 12823 | 3409 | 2015 | 2017 | 2018 |
| hist_gradient_boosting | fold_3 | 2 | 0.384 | 12823 | 3409 | 2015 | 2017 | 2018 |
| hist_gradient_boosting | fold_3 | 3 | 0.380 | 12823 | 3409 | 2015 | 2017 | 2018 |

Winning parameters are recorded in the tuning CSV. The search is intentionally limited to these candidates and is not evidence of exhaustive optimization.

## Calibration, lift, ablation, and interpretation

Calibration deciles and top-risk lift are based on pooled OOF predictions and should be interpreted with fold-wise results because prevalence changes over time. Permutation importance is calculated on outer validation solely as a descriptive diagnostic; it does not select features or hyperparameters. Ablations retain the same rows and use the full model's selected fold parameters. Partial dependence is descriptive, fold-specific, and restricted to the training-support 5th–95th percentile range; it is not causal.

| model | ablation | folds | full_ap | mean_ap | delta_ap | mean_brier |
| --- | --- | --- | --- | --- | --- | --- |
| hist_gradient_boosting | no_acs_controls | 3 | 0.381 | 0.373 | -0.007 | 0.144 |
| hist_gradient_boosting | no_employment_growth | 3 | 0.381 | 0.385 | 0.004 | 0.142 |
| hist_gradient_boosting | no_sector | 3 | 0.381 | 0.281 | -0.100 | 0.153 |
| hist_gradient_boosting | no_startup_rate_lag1 | 3 | 0.381 | 0.376 | -0.004 | 0.143 |
| random_forest | no_acs_controls | 3 | 0.376 | 0.372 | -0.004 | 0.145 |
| random_forest | no_employment_growth | 3 | 0.376 | 0.376 | -0.000 | 0.144 |
| random_forest | no_sector | 3 | 0.376 | 0.287 | -0.089 | 0.152 |
| random_forest | no_startup_rate_lag1 | 3 | 0.376 | 0.370 | -0.007 | 0.145 |

| model | feature | importance_value |
| --- | --- | --- |
| hist_gradient_boosting | sector_code | 0.129 |
| hist_gradient_boosting | startup_rate | 0.082 |
| hist_gradient_boosting | acs_population_growth | 0.024 |
| hist_gradient_boosting | startup_rate_lag1 | 0.011 |
| hist_gradient_boosting | educational_attainment_pct | -0.000 |
| hist_gradient_boosting | unemployment_rate | -0.008 |
| hist_gradient_boosting | labor_force_participation_pct | -0.012 |
| hist_gradient_boosting | median_household_income | -0.012 |
| hist_gradient_boosting | year | -0.014 |
| hist_gradient_boosting | employment_growth | -0.014 |
| random_forest | sector_code | 0.118 |
| random_forest | acs_population_growth | 0.037 |
| random_forest | startup_rate | 0.032 |
| random_forest | startup_rate_lag1 | 0.006 |
| random_forest | educational_attainment_pct | 0.006 |
| random_forest | unemployment_rate | 0.000 |
| random_forest | labor_force_participation_pct | -0.007 |
| random_forest | year | -0.009 |
| random_forest | employment_growth | -0.010 |
| random_forest | median_household_income | -0.011 |

| risk_bin | n | mean_predicted_probability | observed_gap_prevalence |
| --- | --- | --- | --- |
| 1 | 1364 | 0.042 | 0.018 |
| 2 | 1363 | 0.079 | 0.071 |
| 3 | 1363 | 0.108 | 0.104 |
| 4 | 1363 | 0.137 | 0.124 |
| 5 | 1364 | 0.165 | 0.183 |
| 6 | 1363 | 0.193 | 0.194 |
| 7 | 1363 | 0.225 | 0.210 |
| 8 | 1363 | 0.262 | 0.275 |
| 9 | 1363 | 0.310 | 0.321 |
| 10 | 1364 | 0.442 | 0.413 |

| risk_cut | selected_n | observed_gap_prevalence | overall_prevalence | lift_ratio |
| --- | --- | --- | --- | --- |
| 0.100 | 1364 | 0.413 | 0.191 | 2.158 |
| 0.200 | 2727 | 0.367 | 0.191 | 1.919 |
| 0.250 | 3409 | 0.350 | 0.191 | 1.828 |

## Decision and limitations

The locked logistic model remains the reference. The selected nonlinear model's advantage is +0.004 pooled AP with 2/3 fold wins; this is not treated as a final model-selection or deployment decision. Complete-case selection limits the estimand to the retained sample. Temporal OOF results do not establish final holdout generalization. Features are predictive associations, not causal effects.

## Outputs

- Performance and OOF predictions: `reports/tables/a6_advanced_model_performance.csv`, `reports/tables/a6_advanced_oof_predictions.csv`
- Tuning, ablations, importance, calibration, lift, and partial dependence: `reports/tables/a6_advanced_tuning.csv`, `reports/tables/a6_advanced_ablation.csv`, `reports/tables/a6_advanced_permutation_importance.csv`, `reports/tables/a6_advanced_calibration.csv`, `reports/tables/a6_advanced_lift.csv`, `reports/tables/a6_advanced_partial_dependence.csv`
- Figures: `reports/figures/a6_advanced_ap_by_fold.png`, `reports/figures/a6_advanced_brier_by_fold.png`, `reports/figures/a6_advanced_calibration.png`, `reports/figures/a6_advanced_partial_dependence.png`, `reports/figures/a6_advanced_permutation_importance.png`, `reports/figures/a6_advanced_pooled_ap.png`, `reports/figures/a6_advanced_roc_auc_by_fold.png`
