# Assignment 6.6: Robustness, Interpretation & Generalization

## Executive Summary

The primary study remains the A6.3 fold-local p20 exact-t+3 target with simple logistic regression as reference; HistGradientBoosting is the nonlinear sensitivity. Across the checks below, sector context remains a large predictive source, while the growth-measure and model-family rankings vary only modestly. These are development-only stress tests, not causal evidence or final validation. All predictive analyses stop at target year 2020; no 2021–2023 outcomes were queried or scored, and no A6.7 work was started.

## Purpose and safeguards

The temporal folds, target construction, and feature boundary remain unchanged. The A6.4 common complete-case feature sample is used for paired tests when possible. Cutoffs and preprocessing are learned within each fold. The geographic test uses a deterministic SHA-256 hash partition of CBSA codes (hash bucket modulo 10,000; buckets 0–1,999 assigned to test), with temporal training/validation chronology preserved inside each fold. Geographic-test MSAs never appear in any training fold. Only fixed-formula logistic is tested geographically: HGB is omitted because its A6.5 settings were tuned using temporal development folds containing all MSAs.

## Gap-Threshold Robustness

The approved p10, p20, p25, and training residual mean-minus-one-SD labels are taken from A6.3, where thresholds are fold-local and training-only. p20 remains primary. AP is interpreted against each definition's natural prevalence and within-fold prevalence baselines; pooled AP is also affected by fold-level score scale.

| gap_definition | model | sample_n | prevalence | AP | ROC_AUC | Brier | top10_lift | label_agreement_with_p20 | positive_jaccard_with_p20 | cohen_kappa_with_p20 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| p10 | logistic | 13633 | 0.089 | 0.233 | 0.721 | 0.076 | 2.873 | 0.898 | 0.465 | 0.585 |
| p10 | hist_gradient_boosting | 13633 | 0.089 | 0.239 | 0.741 | 0.075 | 2.989 | 0.898 | 0.465 | 0.585 |
| p20_primary | logistic | 13633 | 0.191 | 0.367 | 0.693 | 0.142 | 2.250 | 1.000 | 1.000 | 1.000 |
| p20_primary | hist_gradient_boosting | 13633 | 0.191 | 0.371 | 0.711 | 0.140 | 2.158 | 1.000 | 1.000 | 1.000 |
| p25 | logistic | 13633 | 0.243 | 0.416 | 0.690 | 0.168 | 1.958 | 0.949 | 0.789 | 0.850 |
| p25 | hist_gradient_boosting | 13633 | 0.243 | 0.421 | 0.703 | 0.165 | 1.892 | 0.949 | 0.789 | 0.850 |
| mean_minus_1sd | logistic | 13633 | 0.089 | 0.233 | 0.721 | 0.076 | 2.886 | 0.898 | 0.467 | 0.587 |
| mean_minus_1sd | hist_gradient_boosting | 13633 | 0.089 | 0.238 | 0.739 | 0.075 | 2.985 | 0.898 | 0.467 | 0.587 |

## Expected-Model Robustness

Huber Model C was refit within each frozen first-stage cutoff using the A6.2 formula. Huber p20 thresholds come from that fold's in-sample training residuals; labels are applied to exact development target pairs only. Agreement below compares those labels to Model A p20. This sensitivity does not replace the OLS Model A target.

| fold | n | agreement | positive_jaccard | cohen_kappa | primary_positive_n | alternative_positive_n |
| --- | --- | --- | --- | --- | --- | --- |
| fold_1 | 3599 | 0.958 | 0.818 | 0.874 | 736 | 775 |
| fold_2 | 3591 | 0.967 | 0.859 | 0.903 | 772 | 771 |
| fold_3 | 7223 | 0.966 | 0.830 | 0.886 | 1306 | 1353 |

| model | sample_n | prevalence | AP | ROC_AUC | Brier | top10_lift |
| --- | --- | --- | --- | --- | --- | --- |
| hist_gradient_boosting | 13633 | 0.199 | 0.323 | 0.680 | 0.149 | 1.842 |
| logistic | 13633 | 0.199 | 0.325 | 0.668 | 0.150 | 1.978 |

## Alternative Growth Measures

Employment growth remains primary. Each available QCEW growth measure replaces employment growth one at a time in the logistic and HGB predictor matrix. Rates are annual decimal changes; missingness is the number/share excluded from the candidate's paired rows. No composite is constructed.

| growth_measure | model | sample_n | missing_n | missing_share | prevalence | AP | ROC_AUC | Brier | top10_lift | no_sector_AP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| employment_growth | hist_gradient_boosting | 13633 | 0 | 0.000 | 0.191 | 0.371 | 0.711 | 0.140 | 2.158 | 0.281 |
| employment_growth | logistic | 13633 | 0 | 0.000 | 0.191 | 0.367 | 0.693 | 0.142 | 2.250 | 0.232 |
| establishment_growth | hist_gradient_boosting | 13633 | 0 | 0.000 | 0.191 | 0.376 | 0.714 | 0.140 | 2.242 | 0.281 |
| establishment_growth | logistic | 13633 | 0 | 0.000 | 0.191 | 0.368 | 0.693 | 0.142 | 2.234 | 0.230 |
| payroll_growth | hist_gradient_boosting | 13633 | 0 | 0.000 | 0.191 | 0.373 | 0.712 | 0.140 | 2.192 | 0.278 |
| payroll_growth | logistic | 13633 | 0 | 0.000 | 0.191 | 0.367 | 0.693 | 0.142 | 2.242 | 0.231 |
| wage_growth | hist_gradient_boosting | 13633 | 0 | 0.000 | 0.191 | 0.374 | 0.711 | 0.140 | 2.192 | 0.278 |
| wage_growth | logistic | 13633 | 0 | 0.000 | 0.191 | 0.366 | 0.692 | 0.142 | 2.230 | 0.228 |

## Entrepreneurship-Measure Robustness

The available establishment-entry and startup-job-creation measures are not interchangeable with firm startup rate: they measure establishment flows or job counts, and the existing entry-rate field includes documented values above 100 with unresolved interpretation. A defensible alternate outcome requires a separately specified expected-rate construct, denominator review, and fold-local target build. It is therefore deferred rather than forced into this robustness comparison.

## Pandemic Sensitivity

Sensitivity A removes development pairs whose predictor or target calendar year is 2020. In the frozen development OOF set, predictor years stop at 2017, so this removes only fold-3 validation outcomes with target year 2020. No expected-model training years change: first-stage fit cutoffs are 2016, 2017, and 2018. Sensitivity B excludes years 2020–2021 where present; no development pair has predictor year 2020/2021 or target year 2021, so its development evaluation is identical to A. The 2021 temporal holdout outcome is not read.

| sensitivity | model | sample_n | prevalence | AP | ROC_AUC | Brier | top10_lift | sector_drop_in_AP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| exclude_2020_2021_pairs | hist_gradient_boosting | 10215 | 0.195 | 0.369 | 0.707 | 0.142 | 2.096 | 0.096 |
| exclude_2020_2021_pairs | logistic | 10215 | 0.195 | 0.366 | 0.690 | 0.144 | 2.196 | 0.140 |
| exclude_2020_pairs | hist_gradient_boosting | 10215 | 0.195 | 0.369 | 0.707 | 0.142 | 2.096 | 0.096 |
| exclude_2020_pairs | logistic | 10215 | 0.195 | 0.366 | 0.690 | 0.144 | 2.196 | 0.140 |

## Heavy-Tail Sensitivity

The raw employment-growth specification is compared with a non-destructive training-only 1st/99th percentile clipping sensitivity. Quantile bounds are estimated from each outer training fold and applied to copies of its training and validation fields. Production values and canonical data are unchanged.

| specification | model | sample_n | prevalence | AP | ROC_AUC | Brier | top10_lift | clip_lower | clip_upper |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| training_p01_p99_clip | logistic | 3387 | 0.200 | 0.403 | 0.709 | 0.144 | 2.269 | -0.172 | 0.217 |
| training_p01_p99_clip | hist_gradient_boosting | 3387 | 0.200 | 0.386 | 0.716 | 0.144 | 2.137 | -0.172 | 0.217 |
| training_p01_p99_clip | logistic | 3409 | 0.214 | 0.387 | 0.679 | 0.156 | 2.208 | -0.165 | 0.209 |
| training_p01_p99_clip | hist_gradient_boosting | 3409 | 0.214 | 0.400 | 0.710 | 0.152 | 2.112 | -0.165 | 0.209 |
| training_p01_p99_clip | logistic | 6837 | 0.176 | 0.345 | 0.698 | 0.133 | 2.289 | -0.161 | 0.209 |
| training_p01_p99_clip | hist_gradient_boosting | 6837 | 0.176 | 0.353 | 0.713 | 0.132 | 2.147 | -0.161 | 0.209 |
| raw_primary | logistic | 13633 | 0.191 | 0.367 | 0.693 | 0.142 | 2.250 |  |  |
| training_p01_p99_clip | logistic | 13633 | 0.191 | 0.368 | 0.693 | 0.142 | 2.250 | -0.172 | 0.217 |
| raw_primary | hist_gradient_boosting | 13633 | 0.191 | 0.371 | 0.711 | 0.140 | 2.158 |  |  |
| training_p01_p99_clip | hist_gradient_boosting | 13633 | 0.191 | 0.371 | 0.711 | 0.140 | 2.165 | -0.172 | 0.217 |

## Sector Dependence and Within-Sector Performance

The p20 model without sector is the A6.4 paired ablation; the leave-one-sector-out table separately refits after excluding each sector from training and scores the remaining OOF observations. It is an influence analysis, not unseen-sector validation. Sector-specific AP is reported only with at least 30 positive events; otherwise the row is flagged insufficient. A broader sector mapping was not used because no reviewed defensible grouping is defined in the current design.

| sector_code | n | positive_n | gap_prevalence | AP | ROC_AUC | top10_lift | sufficient_sample |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | 95 | 32 | 0.337 | 0.609 | 0.728 | 2.375 | True |
| 21 | 171 | 97 | 0.567 | 0.897 | 0.899 | 1.665 | True |
| 22 | 241 | 2 | 0.008 |  |  |  | False |
| 23 | 1246 | 173 | 0.139 | 0.248 | 0.695 | 2.017 | True |
| 31-33 | 945 | 168 | 0.178 | 0.205 | 0.557 | 1.303 | True |
| 42 | 570 | 96 | 0.168 | 0.258 | 0.639 | 1.667 | True |
| 44-45 | 1386 | 221 | 0.159 | 0.255 | 0.669 | 1.895 | True |
| 48-49 | 605 | 175 | 0.289 | 0.401 | 0.645 | 1.417 | True |
| 51 | 420 | 104 | 0.248 | 0.499 | 0.684 | 2.404 | True |
| 52 | 889 | 142 | 0.160 | 0.230 | 0.647 | 1.548 | True |
| 53 | 1001 | 209 | 0.209 | 0.325 | 0.676 | 1.849 | True |
| 54 | 812 | 166 | 0.204 | 0.334 | 0.681 | 1.849 | True |
| 55 | 304 | 7 | 0.023 |  |  |  | False |
| 56 | 859 | 195 | 0.227 | 0.307 | 0.624 | 1.485 | True |
| 61 | 389 | 116 | 0.298 | 0.405 | 0.615 | 1.376 | True |
| 62 | 832 | 109 | 0.131 | 0.251 | 0.667 | 2.453 | True |
| 71 | 652 | 191 | 0.293 | 0.367 | 0.602 | 1.345 | True |
| 72 | 1074 | 250 | 0.233 | 0.375 | 0.674 | 1.870 | True |
| 81 | 1142 | 155 | 0.136 | 0.272 | 0.698 | 2.114 | True |

| model | with_sector_AP | without_sector_AP | AP_drop_without_sector |
| --- | --- | --- | --- |
| random_forest | 0.376 | 0.287 | 0.089 |
| hist_gradient_boosting | 0.381 | 0.281 | 0.100 |

Largest leave-one-sector-out changes:

| omitted_sector | oof_n | AP | AP_change_vs_primary | ROC_AUC | top10_lift |
| --- | --- | --- | --- | --- | --- |
| 21 | 13462 | 0.325 | -0.042 | 0.684 | 2.109 |
| 31-33 | 12688 | 0.376 | 0.009 | 0.702 | 2.262 |
| 44-45 | 12247 | 0.376 | 0.008 | 0.695 | 2.241 |
| 81 | 12491 | 0.374 | 0.007 | 0.691 | 2.220 |
| 23 | 12387 | 0.374 | 0.007 | 0.691 | 2.209 |
| 52 | 12744 | 0.373 | 0.006 | 0.695 | 2.245 |
| 51 | 13213 | 0.362 | -0.006 | 0.693 | 2.223 |
| 62 | 12801 | 0.372 | 0.005 | 0.692 | 2.211 |

## Geographic Generalization

The held-out geography partition is fixed by code hash, not outcomes. Within each outer fold, model fitting uses only temporal training rows from training MSAs; evaluation uses only that fold's validation rows from test MSAs. Training and test geography sets have zero overlap. Only fixed-formula logistic is evaluated: HGB is omitted because its A6.5 settings were tuned on temporal folds containing all MSAs. Full ordinary temporal OOF and its training-geography subset are reference rows.

| geography_comparison | model | train_msa_n | test_msa_n | sample_n | prevalence | AP | ROC_AUC | Brier | top10_lift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| unseen_msa | logistic | 290 | 72 | 2750 | 0.204 | 0.408 | 0.710 | 0.146 | 2.196 |
| ordinary_temporal_all_geographies | logistic | 290 | 72 | 13633 | 0.191 | 0.367 | 0.693 | 0.142 | 2.250 |
| ordinary_temporal_train_geographies | logistic | 290 | 72 | 10883 | 0.188 | 0.357 | 0.688 | 0.141 | 2.235 |

## MSA-Size Generalization

MSA population groups use ACS population from predictor year t. Fold-specific tercile cutpoints are estimated from training MSAs only and applied unchanged to validation rows. Therefore the group labels are temporally valid; small and large metro differences remain conditional on the complete-case sample.

| population_group | msa_n | sample_n | prevalence | AP | ROC_AUC | Brier | top10_lift |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lower_third | 121 | 3753 | 0.274 | 0.432 | 0.650 | 0.190 | 1.817 |
| middle_third | 124 | 4658 | 0.222 | 0.347 | 0.643 | 0.165 | 1.763 |
| upper_third | 124 | 5222 | 0.105 | 0.340 | 0.774 | 0.086 | 3.637 |

## Large-Metro Coverage

The existing A5 coverage audit contains 381 MSAs; 314 pass the A5 comparison screen and 67 are thin. Current A6.4-complete OOF coverage is separately counted in the coverage CSV. Major metros with unexpectedly thin coverage include Atlanta (65 rows/6 sectors) and Chicago (95 rows/11 sectors); other large metros such as Los Angeles (265/19), New York (178/14), and Houston (123/16) meet the screen but do not have identical sector coverage. The comparison screen is a descriptive coverage rule, not a model eligibility criterion.

## Complete-Case Selection and Missingness

Included/excluded contrasts below describe the A6.4 extended-feature complete-case selection among otherwise eligible development validation pairs. Continuous-variable standardized differences use pooled within-group standard deviations; categorical sector rows are representation rates, not standardized effects. This analysis does not impute or alter training observations.

| variable | included_n | excluded_n | included_mean_or_share | excluded_mean_or_share | standardized_difference |
| --- | --- | --- | --- | --- | --- |
| acs_population | 13633 | 720 | 807283.863 | 405850.243 | 0.283 |
| startup_rate | 13633 | 780 | 6.589 | 5.650 | 0.232 |
| employment_growth | 13633 | 536 | 0.019 | 0.008 | 0.117 |
| unemployment_rate | 13633 | 720 | 7.981 | 8.069 | -0.035 |
| median_household_income | 13633 | 720 | 52762.838 | 49779.429 | 0.336 |
| sector_share:11 | 13633 | 780 | 0.007 | 0.038 |  |
| sector_share:21 | 13633 | 780 | 0.013 | 0.047 |  |
| sector_share:22 | 13633 | 780 | 0.018 | 0.065 |  |
| sector_share:23 | 13633 | 780 | 0.091 | 0.028 |  |
| sector_share:31-33 | 13633 | 780 | 0.069 | 0.072 |  |
| sector_share:42 | 13633 | 780 | 0.042 | 0.073 |  |
| sector_share:44-45 | 13633 | 780 | 0.102 | 0.010 |  |
| sector_share:48-49 | 13633 | 780 | 0.044 | 0.072 |  |
| sector_share:51 | 13633 | 780 | 0.031 | 0.062 |  |
| sector_share:52 | 13633 | 780 | 0.065 | 0.072 |  |
| sector_share:53 | 13633 | 780 | 0.073 | 0.056 |  |
| sector_share:54 | 13633 | 780 | 0.060 | 0.044 |  |
| sector_share:55 | 13633 | 780 | 0.022 | 0.068 |  |
| sector_share:56 | 13633 | 780 | 0.063 | 0.062 |  |
| sector_share:61 | 13633 | 780 | 0.029 | 0.062 |  |
| sector_share:62 | 13633 | 780 | 0.061 | 0.033 |  |
| sector_share:71 | 13633 | 780 | 0.048 | 0.072 |  |
| sector_share:72 | 13633 | 780 | 0.079 | 0.022 |  |
| sector_share:81 | 13633 | 780 | 0.084 | 0.042 |  |

A core-predictor logistic sensitivity without ACS controls is available in `a6_missingness_core_sensitivity.csv`. It uses a larger sample and is compared descriptively with extended-complete-case performance; the change is not attributed solely to ACS usefulness because sample composition differs.

## Startup-History Sensitivity

The same predictor-year alignment is retained while lag 2 or lag 3 substitutes for lag 1. Their smaller eligible sample sizes are reported and are not compared as if paired with the primary sample.

| startup_history | model | sample_n | prevalence | AP | ROC_AUC | Brier | top10_lift | missing_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | hist_gradient_boosting | 13633 | 0.191 | 0.371 | 0.711 | 0.140 | 2.158 | 0 |
| primary | logistic | 13633 | 0.191 | 0.367 | 0.693 | 0.142 | 2.250 | 0 |
| lag2 substitution | hist_gradient_boosting | 13249 | 0.187 | 0.351 | 0.704 | 0.139 | 2.098 | 384 |
| lag2 substitution | logistic | 13249 | 0.187 | 0.351 | 0.690 | 0.140 | 2.264 | 384 |
| lag3 substitution | hist_gradient_boosting | 13222 | 0.188 | 0.342 | 0.691 | 0.142 | 2.017 | 411 |
| lag3 substitution | logistic | 13222 | 0.188 | 0.340 | 0.678 | 0.143 | 2.082 | 411 |

## Interpretation and robustness scorecard

The logistic coefficient summary retains the A6.4 standardized-feature interpretation; HistGradientBoosting importance/PDP are descriptive and noncausal. A small improvement in a sensitivity is not used to select the primary specification. Employment growth provides economic context and contributes to expected-entrepreneurship construction; weak incremental classification value does not imply economic irrelevance.

| specification | sample_n | prevalence | AP | ROC_AUC | Brier | top10_lift | conclusion_stable | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Three-year p20 signal | 13633 | 0.191 | 0.367 | 0.693 | 0.142 | 2.250 | Robust | Average precision exceeds natural prevalence; predictive, not causal. |
| Sector contribution | 13633 | 0.191 | 0.367 | 0.693 | 0.142 | 2.250 | Generally robust with caveats | No-sector ablation reduces performance; sector 21 is influential. |
| Employment-growth substitution | 13633 | 0.191 | 0.367 | 0.693 | 0.142 | 2.250 | Generally robust with caveats | Alternative growth measures yield similar rankings. |
| High-risk concentration | 13633 | 0.191 | 0.367 | 0.693 | 0.142 | 2.250 | Robust | Top-decile lift indicates ranking concentration, not intervention effects. |
| Nonlinearity (HGB versus logistic) | 13633 | 0.191 | 0.371 | 0.711 | 0.140 | 2.158 | Generally robust with caveats | Pooled AP gain is small and fold-dependent. |
| Expected-model dependence (Huber labels) | 13633 | 0.199 | 0.325 | 0.668 | 0.150 | 1.978 | Sensitive | Fold label agreement is high, but predictive AP is lower. |
| Alternate target: p10 | 13633 | 0.089 | 0.233 | 0.721 | 0.076 | 2.873 | Generally robust with caveats | Natural prevalence and positive-label overlap change. |
| Alternate target: p25 | 13633 | 0.243 | 0.416 | 0.690 | 0.168 | 1.958 | Generally robust with caveats | Natural prevalence and positive-label overlap change. |
| Alternate target: mean_minus_1sd | 13633 | 0.089 | 0.233 | 0.721 | 0.076 | 2.886 | Generally robust with caveats | Natural prevalence and positive-label overlap change. |
| lag2 substitution | 13249 | 0.187 | 0.351 | 0.690 | 0.140 | 2.264 | Generally robust with caveats | 384 validation pairs lost; not a paired comparison. |
| lag3 substitution | 13222 | 0.188 | 0.340 | 0.678 | 0.143 | 2.082 | Generally robust with caveats | 411 validation pairs lost; not a paired comparison. |
| Core predictors without ACS controls | 13696 | 0.191 | 0.378 | 0.696 | 0.145 | 2.225 | Generally robust with caveats | Mean fold metrics; sample composition changes, so not an isolated ACS effect. |

## Limitations and plain-language conclusion

- **Gap definition:** p10, p25, and mean-minus-SD retain the same residual-gap concept but alter prevalence/severity; interpretation must account for each natural rate.
- **Expected benchmark:** the Huber check measures sensitivity to robust regression, not a new target concept; any disagreement narrows construct robustness.
- **Geography and size:** unseen-MSA and tercile tests challenge external validity, but remain within the historical panel and complete-case observations.
- **Selection and coverage:** smaller, low-startup MSAs are more likely to be excluded; thin A5 coverage remains for some large metros.
- **Measurement/design:** startup rate is narrow, sectors are 2-digit NAICS, the residual target is model-dependent, and the 2010–2023 period includes unusual pandemic-era shifts.
- **Inference:** this is predictive, not causal; AP/lift describe ranking, not intervention effects or individual certainty.

Overall, the baseline predictive signal and strong sector contribution are tested across alternate definitions and samples, but small incremental model differences should not be overstated. The geographic test is the most direct check of unseen-MSA transfer. The final temporal holdout remains fully reserved for A6.7.

## Outputs

Report: `reports/assignment6_robustness_generalization.md`; scorecard: `reports/tables/a6_robustness_scorecard.csv`; gap definitions: `reports/tables/a6_robustness_gap_definitions.csv`; geographic: `reports/tables/a6_geographic_generalization.csv`; MSA size: `reports/tables/a6_msa_size_generalization.csv`; selection: `reports/tables/a6_sample_selection_audit.csv`; sectors: `reports/tables/a6_sector_predictive_performance.csv`; runner: `src/regional_entrepreneurship_intelligence/models/run_robustness.py`; logic: `src/regional_entrepreneurship_intelligence/models/robustness.py`.

Figures: `reports/figures/a6_robust_gap_ap.png`, `reports/figures/a6_robust_gap_lift.png`, `reports/figures/a6_robust_huber_target.png`, `reports/figures/a6_robust_huber_label_agreement.png`, `reports/figures/a6_robust_geographic.png`, `reports/figures/a6_robust_msa_size.png`, `reports/figures/a6_robust_sector_ap.png`, `reports/figures/a6_robust_sector_prevalence.png`, `reports/figures/a6_robust_growth_measures.png`, `reports/figures/a6_robust_pandemic.png`, `reports/figures/a6_robust_scorecard_lift.png`, `reports/figures/a6_robust_selection_population.png`

## Readiness for A6.7

A6.6 ends here. No holdout metrics, final model refit, deployment threshold, dashboard, or A6.7 implementation is included.
