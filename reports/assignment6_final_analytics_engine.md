# Assignment 6 Final Analytics Engine

## Executive Summary

The locked simple logistic model achieved holdout AP 0.404 at 23.3% prevalence (AP/prevalence 1.74), ROC-AUC 0.692, Brier 0.164, and top-decile lift 1.99x. Evidence classification: **meaningful**. The final temporal test covers 10,304 complete-case MSA-sector-year observations from 365 MSAs and 19 sectors. The model was not changed after evaluation.

## Research Objective

Predict whether an MSA-industry combination will fall below its expected entrepreneurial activity exactly three years later. The operational outcome is BDS firm startup rate relative to an expected-rate benchmark, not all dimensions of entrepreneurship.

## Final Locked Design

The lock was committed before holdout scoring in `docs/ASSIGNMENT6_FINAL_MODEL_LOCK.md`. Model A is the OLS expected-startup model; the primary predictive model is A6.4 Baseline 1 logistic (`startup_rate`, `startup_rate_lag1`, `employment_growth`, sector contrasts, standardized predictor-year trend). ACS controls are not predictors of the primary model. The frozen A6.5 HistGradientBoosting model is a sensitivity and uses its extended feature family/configuration. Both models use the same A6.4 complete-case analysis population. No tuning, threshold selection, or feature change used holdout outcomes.

## Final Training Population

Development target years end in 2020; classifier predictors end in 2017. There are 31,830 exact candidate pairs, 23,069 complete-case eligible training pairs from 362 MSAs. The classifier sample requires the frozen A6.4 extended completeness rule, although the primary logistic fit itself uses only its locked simple predictors.

## Holdout Construction

Pairs match the same CBSA and sector at predictor year `t` and target year `t+3`. The expected model was fit only on complete observations through 2020. The final p20 threshold is **-1.478345** startup-rate points, calculated as the linear-interpolated 20th percentile of 38,061 in-sample development residuals. For 2021-2023 expected values, the training year-effect rule carries 2020 forward. Target-year covariates are confined to label construction and never enter classifier `X_t`.

## Holdout Sample

There are 12,091 exact calendar candidate pairs; 10,924 have eligible expected-model target labels; 10,304 are complete-case eligible for the locked model comparison. Excluded: 1,787 (14.8%). Holdout prevalence is 23.3%; predictors 2018-2020 map exactly to outcomes 2021-2023. Development and holdout use identical feature eligibility rules.

## Final Logistic Model

The regularized binomial GLM uses training-only means/scales and sector contrasts. The primary diagnostic probability threshold is the final development label prevalence (0.1883); 0.50 is also retained as a diagnostic, not optimized for deployment. The primary threshold metrics in the tables use the frozen prevalence policy.

## Holdout Predictive Performance

| model | N | prevalence | AP | ROC_AUC | Brier | recall | precision | f1 | balanced_accuracy | top10_lift | top20_lift | top25_lift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| prevalence_benchmark | 10304 | 0.233 | 0.233 | 0.500 | 0.180 | 1.000 | 0.233 | 0.377 | 0.500 | 1.000 | 1.000 | 1.000 |
| logistic | 10304 | 0.233 | 0.404 | 0.692 | 0.164 | 0.708 | 0.328 | 0.448 | 0.634 | 1.985 | 1.749 | 1.658 |
| hist_gradient_boosting | 10304 | 0.233 | 0.424 | 0.708 | 0.161 | 0.750 | 0.330 | 0.458 | 0.644 | 2.090 | 1.836 | 1.740 |

Holdout AP is interpreted relative to the observed 23.3% prevalence. Logistic AP is 1.74 times prevalence; AP remains a ranking metric, not a probability-calibration statistic. ROC-AUC 0.692 is above random ranking (0.50), without treating 0.80 as a pass/fail rule. The development-prevalence benchmark's holdout AP is 0.233, equal to the natural prevalence up to tie behavior.

## Comparison with Development

| Metric | Logistic holdout | HGB holdout | Logistic development OOF | Holdout minus development logistic |
| --- | ---: | ---: | ---: | ---: |
| AP | 0.404 | 0.424 | 0.367 | +0.037 |
| ROC-AUC | 0.692 | 0.708 | 0.693 | -0.001 |
| Brier | 0.164 | 0.161 | 0.142 | +0.022 |
| Top-10 lift | 1.985 | 2.090 | 2.250 | -0.264 |

Comparisons reference development OOF from the pre-existing A6.4/A6.5 outputs, which use fold-local targets and fold-specific training-prevalence thresholds. The final refit uses one development-only threshold and its resulting unique development labels; that distinction is retained rather than falsely treating the two label constructions as identical.

## HistGradientBoosting Sensitivity

HGB AP is 0.424, ROC-AUC 0.708, Brier 0.161, top-10 lift 2.09x. Its AP difference from logistic is +0.020. This does not trigger a model switch: complexity was not selected on the holdout, and one temporal result is insufficient to replace the interpretable reference.

## Calibration

Calibration uses score-ranked equal-count deciles; outcomes contribute only the observed rate. See `a6_final_holdout_calibration.csv`. Deviations between mean predicted risk and observed prevalence describe calibration limitations; no holdout recalibration was performed.

## Lift

The lift table reports tie-aware observed prevalence in the top 10%, 20%, and 25%, divided by overall holdout prevalence. Selected counts use ceiling of the corresponding sample fraction. These are prioritization statistics, not causal treatment effects.

## Recall / Precision

At the frozen development-prevalence diagnostic threshold, logistic recall is 0.708, precision 0.328, F1 0.448, and balanced accuracy 0.634; confusion counts are in `a6_final_model_performance.csv`. Threshold 0.50 was also evaluated without selecting between thresholds based on holdout outcomes.

Fixed 0.50 diagnostic results:

| model | threshold_policy | classification_threshold | true_positive | false_positive | true_negative | false_negative | recall | precision | f1 | balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistic | fixed_0.50_diagnostic | 0.500 | 190 | 124 | 7784 | 2206 | 0.079 | 0.605 | 0.140 | 0.532 |
| hist_gradient_boosting | fixed_0.50_diagnostic | 0.500 | 101 | 32 | 7876 | 2295 | 0.042 | 0.759 | 0.080 | 0.519 |

## Performance by Year

| predictor_year | target_year | model | N | prevalence | AP | ROC_AUC | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2018 | 2021 | logistic | 3372 | 0.243 | 0.435 | 0.710 | 0.167 |
| 2018 | 2021 | hist_gradient_boosting | 3372 | 0.243 | 0.449 | 0.722 | 0.165 |
| 2019 | 2022 | logistic | 3432 | 0.181 | 0.355 | 0.695 | 0.137 |
| 2019 | 2022 | hist_gradient_boosting | 3432 | 0.181 | 0.362 | 0.698 | 0.136 |
| 2020 | 2023 | logistic | 3500 | 0.273 | 0.427 | 0.671 | 0.187 |
| 2020 | 2023 | hist_gradient_boosting | 3500 | 0.273 | 0.462 | 0.702 | 0.181 |

Target years 2021, 2022, and 2023 reflect pandemic and post-pandemic conditions. Year-specific fluctuations are descriptive; they are neither removed nor used for retuning and do not establish causal pandemic effects.

## Performance by Sector

| sector | N | positive_N | prevalence | model | AP | ROC_AUC | sufficient_sample_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | 74 | 32 | 0.432 | logistic | 0.794 | 0.766 | True |
| 11 | 74 | 32 | 0.432 | hist_gradient_boosting | 0.717 | 0.695 | True |
| 21 | 130 | 79 | 0.608 | logistic | 0.870 | 0.900 | True |
| 21 | 130 | 79 | 0.608 | hist_gradient_boosting | 0.920 | 0.917 | True |
| 22 | 169 | 3 | 0.018 | logistic |  |  | False |
| 22 | 169 | 3 | 0.018 | hist_gradient_boosting |  |  | False |
| 23 | 960 | 179 | 0.186 | logistic | 0.337 | 0.701 | True |
| 23 | 960 | 179 | 0.186 | hist_gradient_boosting | 0.340 | 0.731 | True |
| 31-33 | 706 | 183 | 0.259 | logistic | 0.323 | 0.606 | True |
| 31-33 | 706 | 183 | 0.259 | hist_gradient_boosting | 0.379 | 0.657 | True |
| 42 | 411 | 121 | 0.294 | logistic | 0.441 | 0.665 | True |
| 42 | 411 | 121 | 0.294 | hist_gradient_boosting | 0.508 | 0.685 | True |
| 44-45 | 1046 | 183 | 0.175 | logistic | 0.319 | 0.734 | True |
| 44-45 | 1046 | 183 | 0.175 | hist_gradient_boosting | 0.363 | 0.741 | True |
| 48-49 | 492 | 131 | 0.266 | logistic | 0.429 | 0.699 | True |
| 48-49 | 492 | 131 | 0.266 | hist_gradient_boosting | 0.377 | 0.672 | True |
| 51 | 315 | 87 | 0.276 | logistic | 0.465 | 0.669 | True |
| 51 | 315 | 87 | 0.276 | hist_gradient_boosting | 0.483 | 0.672 | True |
| 52 | 659 | 139 | 0.211 | logistic | 0.311 | 0.649 | True |
| 52 | 659 | 139 | 0.211 | hist_gradient_boosting | 0.315 | 0.622 | True |
| 53 | 791 | 190 | 0.240 | logistic | 0.312 | 0.624 | True |
| 53 | 791 | 190 | 0.240 | hist_gradient_boosting | 0.361 | 0.672 | True |
| 54 | 593 | 125 | 0.211 | logistic | 0.375 | 0.718 | True |
| 54 | 593 | 125 | 0.211 | hist_gradient_boosting | 0.396 | 0.707 | True |
| 55 | 196 | 11 | 0.056 | logistic |  |  | False |
| 55 | 196 | 11 | 0.056 | hist_gradient_boosting |  |  | False |
| 56 | 654 | 132 | 0.202 | logistic | 0.260 | 0.596 | True |
| 56 | 654 | 132 | 0.202 | hist_gradient_boosting | 0.279 | 0.638 | True |
| 61 | 303 | 110 | 0.363 | logistic | 0.458 | 0.621 | True |
| 61 | 303 | 110 | 0.363 | hist_gradient_boosting | 0.483 | 0.649 | True |
| 62 | 629 | 95 | 0.151 | logistic | 0.239 | 0.679 | True |
| 62 | 629 | 95 | 0.151 | hist_gradient_boosting | 0.237 | 0.672 | True |
| 71 | 506 | 205 | 0.405 | logistic | 0.472 | 0.586 | True |
| 71 | 506 | 205 | 0.405 | hist_gradient_boosting | 0.506 | 0.623 | True |
| 72 | 814 | 257 | 0.316 | logistic | 0.358 | 0.578 | True |
| 72 | 814 | 257 | 0.316 | hist_gradient_boosting | 0.393 | 0.601 | True |
| 81 | 856 | 134 | 0.157 | logistic | 0.309 | 0.730 | True |
| 81 | 856 | 134 | 0.157 | hist_gradient_boosting | 0.339 | 0.747 | True |

Sector metrics are withheld where positive events are below 30 or no negative cases remain. Sector heterogeneity is informative, but some cell metrics remain unstable.

## Performance by MSA Size

| msa_size_group | MSA_count | N | prevalence | model | AP | ROC_AUC | Brier | top10_lift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| middle | 131 | 3550 | 0.257 | logistic | 0.395 | 0.651 | 0.182 | 1.794 |
| middle | 131 | 3550 | 0.257 | hist_gradient_boosting | 0.403 | 0.655 | 0.180 | 1.849 |
| large | 127 | 3968 | 0.166 | logistic | 0.348 | 0.736 | 0.125 | 2.294 |
| large | 127 | 3968 | 0.166 | hist_gradient_boosting | 0.382 | 0.766 | 0.121 | 2.552 |
| small | 119 | 2786 | 0.296 | logistic | 0.462 | 0.662 | 0.196 | 1.806 |
| small | 119 | 2786 | 0.296 | hist_gradient_boosting | 0.480 | 0.673 | 0.191 | 1.854 |

Size groups follow A6.6: MSA-level median predictor-year population among eligible development MSAs defines 1/3 and 2/3 cutpoints, then holdout predictor-year population is assigned to small/middle/large. Cutpoints are training-only; differences are conditional on complete cases.

## Robustness Summary

A6.6 found p10/p25/mean-minus-SD target definitions retained ranking signal; Huber-based labels agreed about 96% with OLS labels; sector identity was strongly informative; high-risk lift persisted; and geographic/size performance varied. Complete-case selection was patterned. These findings motivate qualified claims, not certainty.

## Research Question and Hypothesis Assessment

| research_item | status | evidence | interpretation |
| --- | --- | --- | --- |
| Primary research question | supported | Holdout AP relative to natural prevalence and secondary ranking discrimination | Predictive association only; no causal claim. |
| H1: predictors improve over baseline | supported | Locked logistic compared with development-prevalence benchmark on identical holdout rows | Incremental predictive value, conditional on complete cases. |
| H2: industry growth positively associated with entrepreneurship | descriptive support only | A5 descriptive association and A6.2 expected-startup specification | Association does not establish that growth causes entrepreneurship. |
| H3: prior entrepreneurship reduces future gap risk | descriptive support only | Lag-1 startup-rate predictor and A6.6 startup-history sensitivity | Predictive signal is not a causal effect. |
| H4: industry relationships vary by sector | partially supported | Development sector ablation and supported-event holdout sector metrics | Subgroup estimates are descriptive and may be unstable. |

H1 is evaluated against the natural-prevalence benchmark on the same holdout sample. H2-H4 are assessed as descriptive/predictive associations using the prior A5/A6 analyses; none is a causal test.

## Practical Interpretation

The model is an early-warning and prioritization aid for identifying MSA-industry combinations that appear at elevated risk of future entrepreneurial under-response relative to observable economic conditions. It is not deterministic and should not be used as an automatic allocation rule.

## Limitations

Firm startup rate is narrower than entrepreneurship broadly; sectors are aggregated to 2-digit NAICS; complete-case selection excludes a patterned subset; metro and sector coverage is uneven; and the historical 2010-2023 period may not generalize to future regimes. Calibration and subgroup performance need scrutiny. Predictive associations do not identify interventions or causes.

## What the Model Can Claim

- Within this eligible historical holdout, it can rank future gap risk above the natural-prevalence-only benchmark when AP exceeds prevalence and lift is above one.
- Sector and entrepreneurial history contain predictive information in the analyzed sample.
- The top-risk groups can concentrate observed future gaps, subject to reported lift and calibration.

## What the Model Cannot Claim

- It cannot claim causality, universal generalizability, perfect case identification, comprehensive entrepreneurship coverage, or equal performance across all MSAs/sectors.
- It cannot guarantee performance outside the observed historical context without new validation.
- It does not measure every startup outcome or within-sector variation below 2-digit NAICS.

## Assignment 6 Completion

The final holdout was evaluated only after the model lock commit. No post-holdout model changes or Assignment 7/dashboard work are included. Outputs are reproducible from the locked runner; historical A6.1-A6.6 artifacts remain frozen.

Figures: `reports/figures/a6_final_ap_comparison.png`, `reports/figures/a6_final_roc_auc_comparison.png`, `reports/figures/a6_final_brier_comparison.png`, `reports/figures/a6_final_precision_recall.png`, `reports/figures/a6_final_roc_curve.png`, `reports/figures/a6_final_calibration.png`, `reports/figures/a6_final_risk_deciles.png`, `reports/figures/a6_final_lift.png`, `reports/figures/a6_final_by_year.png`, `reports/figures/a6_final_by_msa_size.png`
