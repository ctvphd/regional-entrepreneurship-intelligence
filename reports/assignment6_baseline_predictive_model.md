# Assignment 6.4: Baseline Predictive Model

## Executive Summary

This step fits only the training-prevalence benchmark and interpretable logistic regressions. The final holdout was not queried; only predictor years through 2017 were read from the analytical view. The primary metric is Average Precision (AP/PR-AUC), interpreted against the roughly 20% natural prevalence. Pooled OOF AP was 0.183 for Baseline 0, 0.367 for the simple logistic model, and 0.366 for the extended model. The extended-model AP change over prevalence is +0.183; conclusions below reflect that size and fold stability, not accuracy.

## Predictive Objective and Modeling Sample

The unchanged A6.3 `gap_p20` label is predicted at exact same-MSA/same-sector t+3. Predictor rows are joined only at t. Each validation pair receives one prediction from a model trained on that fold's earlier target outcomes. Fold 1-3 are reported separately and pooled results are pooled out-of-fold development metrics, not holdout results.

The A6.3 target artifact has 67,067 fold/split records, including repeated expanding training sets; unique development validation rows are 14,413. The shared feature-complete modeling validation N is 13,633. The extended specification adds five ACS fields; the common-sample rule keeps simple and extended comparisons paired. `a6_baseline_sample_audit.csv` reports per-fold A6.3 eligible pairs and extra predictor-feature exclusions. A6.3's target eligibility itself is already selective: excluded rows were smaller and lower-startup. This analysis cannot restore those rows; performance applies only to complete-case eligible MSA-sector pairs and may not generalize to systematically excluded smaller/lower-startup observations.

| fold | split_role | a6_eligible_n | model_complete_n | additional_missing_n | additional_missing_share |
| --- | --- | --- | --- | --- | --- |
| fold_1 | training | 13955 | 9436 | 4519 | 0.324 |
| fold_1 | validation | 3599 | 3387 | 212 | 0.059 |
| fold_2 | training | 17554 | 12823 | 4731 | 0.270 |
| fold_2 | validation | 3591 | 3409 | 182 | 0.051 |
| fold_3 | training | 21145 | 16232 | 4913 | 0.232 |
| fold_3 | validation | 7223 | 6837 | 386 | 0.053 |

Modeling sample composition by target-feature completeness:

| model_feature_complete | sector_code | n | mean_startup_rate | mean_employment_growth | mean_acs_population |
| --- | --- | --- | --- | --- | --- |
| False | 11 | 30.000 | 8.923 | -0.012 | 400963.517 |
| False | 21 | 37.000 | 1.451 | 0.002 | 359409.378 |
| False | 22 | 51.000 | 0.271 | -0.007 | 468482.103 |
| False | 23 | 22.000 | 6.769 | 0.104 | 372365.862 |
| False | 31-33 | 56.000 | 5.227 | -0.002 | 196945.984 |
| False | 42 | 57.000 | 4.038 | 0.012 | 298788.312 |
| False | 44-45 | 8.000 | 5.468 | 0.006 | 168866.542 |
| False | 48-49 | 56.000 | 8.365 | 0.015 | 323559.691 |
| False | 51 | 48.000 | 5.804 | -0.056 | 332519.574 |
| False | 52 | 56.000 | 4.676 | 0.007 | 327306.927 |
| False | 53 | 44.000 | 6.698 | 0.013 | 368495.381 |
| False | 54 | 34.000 | 6.666 | 0.041 | 478711.199 |
| False | 55 | 53.000 | 0.296 | 0.006 | 363077.907 |
| False | 56 | 48.000 | 7.432 | 0.027 | 738777.570 |
| False | 61 | 48.000 | 8.049 | 0.026 | 367791.921 |
| False | 62 | 26.000 | 5.798 | 0.017 | 1126191.065 |
| False | 71 | 56.000 | 10.544 | 0.058 | 300812.954 |
| False | 72 | 17.000 | 8.672 | 0.018 | 660320.314 |
| False | 81 | 33.000 | 5.406 | -0.012 | 610414.730 |
| True | 11 | 95.000 | 8.781 | 0.024 | 2016862.137 |
| True | 21 | 171.000 | 3.363 | -0.018 | 652068.164 |
| True | 22 | 241.000 | 0.492 | 0.002 | 665980.191 |
| True | 23 | 1246.000 | 7.756 | 0.041 | 642673.054 |
| True | 31-33 | 945.000 | 4.737 | 0.012 | 821766.451 |
| True | 42 | 570.000 | 4.250 | 0.012 | 799551.982 |
| True | 44-45 | 1386.000 | 5.767 | 0.011 | 715422.442 |
| True | 48-49 | 605.000 | 9.006 | 0.034 | 715364.544 |
| True | 51 | 420.000 | 7.787 | -0.002 | 1430296.290 |
| True | 52 | 889.000 | 5.138 | 0.006 | 955132.492 |
| True | 53 | 1001.000 | 8.083 | 0.019 | 828171.280 |
| True | 54 | 812.000 | 7.074 | 0.016 | 650420.032 |
| True | 55 | 304.000 | 0.350 | 0.051 | 825796.339 |
| True | 56 | 859.000 | 7.955 | 0.018 | 670143.694 |
| True | 61 | 389.000 | 8.449 | 0.027 | 1376713.067 |
| True | 62 | 832.000 | 5.340 | 0.021 | 737036.445 |
| True | 71 | 652.000 | 9.539 | 0.031 | 1059059.008 |
| True | 72 | 1074.000 | 8.795 | 0.024 | 705816.926 |
| True | 81 | 1142.000 | 5.507 | 0.012 | 747509.364 |

## Baseline 0: Training Prevalence

For each fold, the probability is the natural gap prevalence in that fold's training labels, applied unchanged to its validation rows. No class rebalancing is used. Within each fold, constant-score AP equals that fold's validation prevalence and ROC-AUC is 0.50. Pooled OOF fold-specific probabilities can rank folds relative to each other, so pooled Baseline 0 AP (0.183) need not equal pooled prevalence (0.191); this cross-fold ranking is still only the predeclared prevalence benchmark, not within-fold discrimination.

## Baseline 1: Simple Logistic

Predictors: predictor-year startup rate, startup-rate lag 1, employment growth, sector fixed effects, and a linear predictor-year trend. Continuous variables are standardized from training rows only; sector levels are learned from training rows, with unseen validation levels safely encoded as all-zero reference contrasts. A tiny L2 penalty stabilizes binomial estimates; classes are not weighted.

## Baseline 2: Extended Logistic

Adds predictor-year population growth, median household income, educational attainment, labor-force participation, and unemployment to Baseline 1. Uses the same common complete-feature sample and training-only transforms. No MSA fixed effects or alternate growth series are used.

## Temporal Validation and Fold Performance

The primary probability scores are shown once per model/fold; threshold-specific recall, precision, F1, balanced accuracy and confusion counts are reported at 0.50 and the fold's training prevalence. Neither is a final operating threshold.

| model | fold | train_n | validation_n | train_prevalence | validation_prevalence | pr_auc | roc_auc | brier_score | recall | precision | f1 | balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_0_prevalence | fold_1 | 9436.000 | 3387 | 0.185 | 0.200 | 0.200 | 0.500 | 0.160 | 1.000 | 0.200 | 0.334 | 0.500 |
| baseline_1_simple | fold_1 | 9436.000 | 3387 | 0.185 | 0.200 | 0.403 | 0.709 | 0.144 | 0.622 | 0.318 | 0.421 | 0.644 |
| baseline_2_extended | fold_1 | 9436.000 | 3387 | 0.185 | 0.200 | 0.402 | 0.710 | 0.144 | 0.634 | 0.318 | 0.423 | 0.647 |
| baseline_0_prevalence | fold_2 | 12823.000 | 3409 | 0.186 | 0.214 | 0.214 | 0.500 | 0.169 | 1.000 | 0.214 | 0.352 | 0.500 |
| baseline_1_simple | fold_2 | 12823.000 | 3409 | 0.186 | 0.214 | 0.387 | 0.680 | 0.156 | 0.569 | 0.320 | 0.410 | 0.620 |
| baseline_2_extended | fold_2 | 12823.000 | 3409 | 0.186 | 0.214 | 0.385 | 0.682 | 0.156 | 0.588 | 0.316 | 0.411 | 0.621 |
| baseline_0_prevalence | fold_3 | 16232.000 | 6837 | 0.188 | 0.176 | 0.176 | 0.500 | 0.145 | 1.000 | 0.176 | 0.299 | 0.500 |
| baseline_1_simple | fold_3 | 16232.000 | 6837 | 0.188 | 0.176 | 0.345 | 0.698 | 0.133 | 0.672 | 0.265 | 0.380 | 0.637 |
| baseline_2_extended | fold_3 | 16232.000 | 6837 | 0.188 | 0.176 | 0.344 | 0.697 | 0.134 | 0.679 | 0.263 | 0.379 | 0.637 |

Confusion counts at each diagnostic threshold (thresholds are not deployment choices):

| model | fold | threshold_policy | classification_threshold | true_positive | false_positive | true_negative | false_negative | recall | precision | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_0_prevalence | fold_1 | 0.50 | 0.500 | 0 | 0 | 2709 | 678 | 0.000 | 0.000 | 0.000 |
| baseline_0_prevalence | fold_1 | train_prevalence | 0.185 | 678 | 2709 | 0 | 0 | 1.000 | 0.200 | 0.334 |
| baseline_1_simple | fold_1 | 0.50 | 0.500 | 51 | 34 | 2675 | 627 | 0.075 | 0.600 | 0.134 |
| baseline_1_simple | fold_1 | train_prevalence | 0.185 | 422 | 904 | 1805 | 256 | 0.622 | 0.318 | 0.421 |
| baseline_2_extended | fold_1 | 0.50 | 0.500 | 49 | 31 | 2678 | 629 | 0.072 | 0.613 | 0.129 |
| baseline_2_extended | fold_1 | train_prevalence | 0.185 | 430 | 924 | 1785 | 248 | 0.634 | 0.318 | 0.423 |
| baseline_0_prevalence | fold_2 | 0.50 | 0.500 | 0 | 0 | 2680 | 729 | 0.000 | 0.000 | 0.000 |
| baseline_0_prevalence | fold_2 | train_prevalence | 0.186 | 729 | 2680 | 0 | 0 | 1.000 | 0.214 | 0.352 |
| baseline_1_simple | fold_2 | 0.50 | 0.500 | 45 | 23 | 2657 | 684 | 0.062 | 0.662 | 0.113 |
| baseline_1_simple | fold_2 | train_prevalence | 0.186 | 415 | 880 | 1800 | 314 | 0.569 | 0.320 | 0.410 |
| baseline_2_extended | fold_2 | 0.50 | 0.500 | 46 | 26 | 2654 | 683 | 0.063 | 0.639 | 0.115 |
| baseline_2_extended | fold_2 | train_prevalence | 0.186 | 429 | 930 | 1750 | 300 | 0.588 | 0.316 | 0.411 |
| baseline_0_prevalence | fold_3 | 0.50 | 0.500 | 0 | 0 | 5636 | 1201 | 0.000 | 0.000 | 0.000 |
| baseline_0_prevalence | fold_3 | train_prevalence | 0.188 | 1201 | 5636 | 0 | 0 | 1.000 | 0.176 | 0.299 |
| baseline_1_simple | fold_3 | 0.50 | 0.500 | 97 | 72 | 5564 | 1104 | 0.081 | 0.574 | 0.142 |
| baseline_1_simple | fold_3 | train_prevalence | 0.188 | 807 | 2242 | 3394 | 394 | 0.672 | 0.265 | 0.380 |
| baseline_2_extended | fold_3 | 0.50 | 0.500 | 93 | 81 | 5555 | 1108 | 0.077 | 0.534 | 0.135 |
| baseline_2_extended | fold_3 | train_prevalence | 0.188 | 816 | 2289 | 3347 | 385 | 0.679 | 0.263 | 0.379 |

## Pooled Out-of-Fold Performance

Each of the 13,633 validation rows appears once in the pooled OOF artifact. The table uses a fold-specific training-prevalence diagnostic threshold; probabilities themselves are evaluated without thresholding.

| model | train_n | validation_n | train_prevalence | validation_prevalence | pr_auc | roc_auc | brier_score | recall | precision | f1 | balanced_accuracy | classification_threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_0_prevalence |  | 13633 |  | 0.191 | 0.183 | 0.477 | 0.155 | 1.000 | 0.191 | 0.321 | 0.500 | 0.187 |
| baseline_1_simple |  | 13633 |  | 0.191 | 0.367 | 0.693 | 0.142 | 0.630 | 0.290 | 0.397 | 0.633 | 0.187 |
| baseline_2_extended |  | 13633 |  | 0.191 | 0.366 | 0.693 | 0.142 | 0.642 | 0.288 | 0.398 | 0.633 | 0.187 |

## PR-AUC Interpretation and Probability Calibration

Pooled AP is compared with actual pooled validation prevalence (0.191). Baseline 1 exceeds the pooled fold-specific prevalence model AP by +0.184, and the extended model by +0.183; relative to the raw pooled positive-class prevalence, the gains are +0.176 and +0.175. Both logistic gains are positive and directionally consistent in all three folds. Pooled prevalence-baseline scores differ across folds, so pooled baseline metrics also reflect cross-fold prevalence ranking; fold-level comparison is the cleaner no-information reference. ROC-AUC and Brier score are secondary; Brier is sensitive to the observed prevalence shift relative to each fold's training prevalence.

Pooled calibration uses equal-frequency risk deciles. The figure and CSV show mean predicted risk versus observed gap prevalence; calibration should be read alongside ranking, since a model can rank without calibrated probabilities.

| risk_bin | n | mean_predicted_probability | observed_gap_prevalence |
| --- | --- | --- | --- |
| 1 | 1364 | 0.039 | 0.041 |
| 2 | 1363 | 0.085 | 0.076 |
| 3 | 1363 | 0.112 | 0.115 |
| 4 | 1363 | 0.135 | 0.139 |
| 5 | 1364 | 0.158 | 0.169 |
| 6 | 1363 | 0.181 | 0.202 |
| 7 | 1363 | 0.208 | 0.207 |
| 8 | 1363 | 0.242 | 0.236 |
| 9 | 1363 | 0.299 | 0.302 |
| 10 | 1364 | 0.462 | 0.424 |

## Recall / Precision Tradeoff, Risk Bins, and Lift

Recall is reported beside precision and F1 because missed gaps are substantively costly. The diagnostic thresholds are 0.50 and training prevalence only; no validation-tuned threshold is selected. Top-risk lift is measured against pooled natural prevalence, with top 10%, 20%, and 25% groups selected by rank.

| model | risk_cut | selected_n | observed_gap_prevalence | overall_prevalence | lift_ratio |
| --- | --- | --- | --- | --- | --- |
| baseline_0_prevalence | 0.100 | 1364 | 0.176 | 0.191 | 0.918 |
| baseline_0_prevalence | 0.200 | 2727 | 0.176 | 0.191 | 0.918 |
| baseline_0_prevalence | 0.250 | 3409 | 0.176 | 0.191 | 0.918 |
| baseline_1_simple | 0.100 | 1364 | 0.430 | 0.191 | 2.250 |
| baseline_1_simple | 0.200 | 2727 | 0.366 | 0.191 | 1.915 |
| baseline_1_simple | 0.250 | 3409 | 0.340 | 0.191 | 1.779 |
| baseline_2_extended | 0.100 | 1364 | 0.424 | 0.191 | 2.219 |
| baseline_2_extended | 0.200 | 2727 | 0.363 | 0.191 | 1.898 |
| baseline_2_extended | 0.250 | 3409 | 0.343 | 0.191 | 1.791 |

## Predictor Contribution and Coefficients

The following ablations are descriptive fold comparisons, not causal effects. They check lag-1 startup history, employment growth, regional controls, sector identity, and time trend contribution while preserving the paired sample.

| model | fold | pr_auc | roc_auc | brier_score |
| --- | --- | --- | --- | --- |
| baseline_0_prevalence | fold_1 | 0.200 | 0.500 | 0.160 |
| baseline_1_simple | fold_1 | 0.403 | 0.709 | 0.144 |
| baseline_2_extended | fold_1 | 0.402 | 0.710 | 0.144 |
| baseline_0_prevalence | fold_2 | 0.214 | 0.500 | 0.169 |
| baseline_1_simple | fold_2 | 0.387 | 0.680 | 0.156 |
| baseline_2_extended | fold_2 | 0.385 | 0.682 | 0.156 |
| baseline_0_prevalence | fold_3 | 0.176 | 0.500 | 0.145 |
| baseline_1_simple | fold_3 | 0.345 | 0.698 | 0.133 |
| baseline_2_extended | fold_3 | 0.344 | 0.697 | 0.134 |
| baseline_2_no_startup_lag1 | fold_1 | 0.385 | 0.699 | 0.146 |
| baseline_2_no_employment_growth | fold_1 | 0.401 | 0.710 | 0.144 |
| baseline_1_no_sector | fold_1 | 0.235 | 0.568 | 0.159 |
| baseline_1_no_time | fold_1 | 0.403 | 0.709 | 0.144 |
| baseline_2_no_startup_lag1 | fold_2 | 0.381 | 0.670 | 0.157 |
| baseline_2_no_employment_growth | fold_2 | 0.384 | 0.681 | 0.156 |
| baseline_1_no_sector | fold_2 | 0.255 | 0.569 | 0.168 |
| baseline_1_no_time | fold_2 | 0.387 | 0.680 | 0.156 |
| baseline_2_no_startup_lag1 | fold_3 | 0.329 | 0.686 | 0.135 |
| baseline_2_no_employment_growth | fold_3 | 0.345 | 0.696 | 0.134 |
| baseline_1_no_sector | fold_3 | 0.207 | 0.568 | 0.144 |
| baseline_1_no_time | fold_3 | 0.344 | 0.697 | 0.133 |

Across folds, adding the five ACS controls does not improve AP (extended minus simple is slightly negative each fold, about 0.001-0.002); Brier changes are tiny and mixed. Removing lag-1 startup rate lowers AP by about 0.004-0.022, while removing employment growth changes AP by less than about 0.002. Removing sector effects substantially lowers AP and ROC-AUC; removing the linear time trend changes little. This first pass suggests strong sector context and startup-history signal, but little incremental gain from current employment growth or the ACS block on this sample.

Continuous coefficients are standardized log-odds changes per one training-fold standard deviation; odds ratios are `exp(coefficient)`. The range and sign consistency below summarize fold stability. Sector contrasts use the first training category as the reference. Coefficients reflect correlated predictors and this selected sample, and are not causal estimates. The full fold coefficient table includes sector and time terms.

| model | variable | mean_coefficient | mean_odds_ratio_per_training_sd | min_coefficient | max_coefficient | positive_folds | folds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_1_simple | employment_growth | -0.031 | 0.970 | -0.045 | -0.020 | 0 | 3 |
| baseline_1_simple | startup_rate | -0.524 | 0.592 | -0.545 | -0.504 | 0 | 3 |
| baseline_1_simple | startup_rate_lag1 | -0.327 | 0.721 | -0.332 | -0.319 | 0 | 3 |
| baseline_1_simple | year_trend | 0.021 | 1.022 | 0.002 | 0.059 | 3 | 3 |
| baseline_2_extended | acs_population_growth | -0.037 | 0.964 | -0.042 | -0.033 | 0 | 3 |
| baseline_2_extended | educational_attainment_pct | 0.036 | 1.037 | 0.030 | 0.049 | 3 | 3 |
| baseline_2_extended | employment_growth | -0.028 | 0.973 | -0.042 | -0.017 | 0 | 3 |
| baseline_2_extended | labor_force_participation_pct | -0.104 | 0.902 | -0.117 | -0.082 | 0 | 3 |
| baseline_2_extended | median_household_income | -0.071 | 0.931 | -0.085 | -0.055 | 0 | 3 |
| baseline_2_extended | startup_rate | -0.517 | 0.596 | -0.539 | -0.498 | 0 | 3 |
| baseline_2_extended | startup_rate_lag1 | -0.323 | 0.724 | -0.330 | -0.314 | 0 | 3 |
| baseline_2_extended | unemployment_rate | -0.036 | 0.965 | -0.057 | 0.002 | 1 | 3 |
| baseline_2_extended | year_trend | 0.012 | 1.012 | -0.003 | 0.041 | 1 | 3 |

## Plain-Language Summary

- **Can gaps be predicted?** Yes, at a useful baseline level in development: simple/extended pooled AP is 0.367/0.366, versus 0.183 for the fold-specific prevalence benchmark, and each fold improves AP.
- **How much better than guessing?** The simple model's pooled AP gain is 0.184 over the fold-specific prevalence model and 0.176 over the raw pooled 19.1% prevalence. This is meaningful ranking signal, not evidence of holdout generalization.
- **Which variables appear useful?** Sector identity has the largest ablation effect; current and lagged startup rates carry stable negative associations with later gap odds. Interpret these as conditional associations, not causes.
- **Does industry growth add value?** Little in this first pass: removing employment growth changes AP by less than about 0.002 across folds.
- **Does startup history dominate?** It contributes, but prediction does not collapse without lag-1; removing it lowers AP by roughly 0.004-0.022 by fold.
- **Are predicted probabilities reasonably calibrated?** The extended-model risk-bin rates broadly track predicted probabilities, though the highest decile's observed prevalence (42.4%) is below its mean predicted risk (46.2%).
- **Can it rank high-risk combinations?** The simple model's top 10% contains 43.0% gaps, about 2.25 times the pooled 19.1% prevalence; top-20% and top-25% lift are about 1.91 and 1.78.

## Limitations, Holdout Preservation, and Leakage Audit

- Complete-case selection is patterned; excluded observations disproportionately come from smaller MSAs and lower startup rates. No imputation was performed.
- Predictor fields are joined by exact `cbsa_code`, `sector_code`, and `predictor_year`; target-year startup, residual, expected rate, margin, and label are excluded from X.
- Numeric scaling statistics and sector categories are fitted within each training fold. Validation labels are used only for evaluation.
- Baseline prevalence and diagnostic classification thresholds use training labels only. No threshold tuning uses validation outcomes.
- The SQLite view was opened read-only and queried only for years through 2017. No 2018-2020 predictors or 2021-2023 outcomes, holdout prevalence, or holdout scores were read.
- No Random Forest, Gradient Boosting, XGBoost, broad hyperparameter tuning, or A6.5 work was performed.

## Readiness for A6.5

The baseline comparison is established under the frozen temporal folds. Whether non-linear models are justified depends on the size/stability of AP gains over natural prevalence, risk-bin concentration, calibration, and paired ablation results above. This step does not claim generalization beyond the selected complete-case population or evaluate the final holdout.

## Outputs

- Report: `reports/assignment6_baseline_predictive_model.md`
- Performance: `reports/tables/a6_baseline_model_performance.csv`
- OOF predictions: `reports/tables/a6_baseline_oof_predictions.csv`
- Coefficients: `reports/tables/a6_baseline_logistic_coefficients.csv`
- Calibration: `reports/tables/a6_baseline_calibration.csv`
- Lift: `reports/tables/a6_baseline_lift.csv`
- Sample audits: `reports/tables/a6_baseline_sample_audit.csv`, `reports/tables/a6_baseline_sector_composition.csv`
- Figures: `reports/figures/a6_baseline_pr_auc_by_fold.png`, `reports/figures/a6_baseline_roc_auc_by_fold.png`, `reports/figures/a6_baseline_brier_by_fold.png`, `reports/figures/a6_baseline_precision_recall.png`, `reports/figures/a6_baseline_roc_curve.png`, `reports/figures/a6_baseline_calibration.png`, `reports/figures/a6_baseline_risk_deciles.png`, `reports/figures/a6_baseline_lift.png`, `reports/figures/a6_baseline_coefficients.png`
- Runner and reusable logic: `src/regional_entrepreneurship_intelligence/models/run_baseline.py`, `src/regional_entrepreneurship_intelligence/models/baseline.py`
