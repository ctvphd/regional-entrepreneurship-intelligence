# Assignment 6.3: Entrepreneurial-Gap Target Construction

## Executive Summary

The development-only A6.3 target was constructed using the selected A6.2 Model A independently within each of the three frozen temporal folds. The primary label is `gap_p20 = 1` when the fold-local alignment residual is less than or equal to that fold's training residual p20. Exact same-MSA/same-sector t-to-t+3 pairs only. The final holdout (2021-2023 outcomes) was excluded from target construction and all diagnostics. No predictive model was trained.

There are 49,754 source panel rows through the permitted development target cutoff (2020). The p20 thresholds have 22,450-30,230 complete-case training residuals. Pooled development validation prevalence is 19.5% (2,814/14,413) when available; training-row prevalence is reported fold-by-fold in the tables and is approximately one-fifth by construction, with inclusive ties.

## Target Construction Objective

Residual is observed startup rate minus expected startup rate. Positive means above expectation; negative means below expectation. A negative residual alone is not classified as a gap. The first-stage model is refit per fold, and no full-sample residual distribution is used.

## Expected-Entrepreneurship Benchmark

Model A is the A6.2 selection: OLS with `startup_rate_lag1`, `employment_growth`, five ACS controls, sector fixed effects, and year fixed effects. Fits use complete cases only. For future validation years without estimated year coefficients, the documented A6.2 rule carries forward the latest training-year effect. Training residuals are fitted/in-sample; validation residuals are out-of-sample. This difference is retained and noted in interpretation.

## Alignment Residual and Primary Gap Definition

`alignment_residual = observed_target_startup_rate - expected_target_startup_rate`.

For fold `k`, thresholds are computed from finite Model A training residuals only. The primary cutoff is the training p20 and labels use `residual <= cutoff`, including ties. The cutoff is not recalculated for validation rows. Robustness cutoffs are p10, p25, and training mean minus one sample standard deviation; p20 remains primary regardless of later predictive performance.

## Fold-Specific Thresholds

| fold | train_n | residual_mean | residual_sd | residual_p10 | residual_p20 | residual_p25 | residual_minus_1sd | primary_threshold | training_residual_gap_prevalence | abs_change_from_previous | relative_change_from_previous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fold_1 | 22450 | -0.000 | 2.358 | -2.354 | -1.470 | -1.164 | -2.358 | -1.470 | 0.200 |  |  |
| fold_2 | 26337 | -0.000 | 2.334 | -2.345 | -1.467 | -1.161 | -2.334 | -1.467 | 0.200 | 0.003 | 0.002 |
| fold_3 | 30230 | -0.000 | 2.343 | -2.353 | -1.476 | -1.163 | -2.343 | -1.476 | 0.200 | 0.009 | 0.006 |

Threshold stability is evaluated by the absolute/relative changes above; relative changes use the absolute previous p20 denominator and are undefined if it is zero. Direction stability: all p20 cutoffs are negative. No requirement for identical fold cutoffs is imposed.

## Gap Prevalence and Target Balance

Pooled validation p20 prevalence: 19.5% across 14,413 complete target pairs. No prevalence normalization or rebalancing was applied.

| fold | eligible_n | gap_n | non_gap_n | gap_non_gap_ratio |
| --- | --- | --- | --- | --- |
| fold_1 | 3599 | 736 | 2863 | 0.257 |
| fold_2 | 3591 | 772 | 2819 | 0.274 |
| fold_3 | 7223 | 1306 | 5917 | 0.221 |
| pooled_development_validation | 14413 | 2814 | 11599 | 0.243 |

Validation prevalence by year:

| target_year | eligible_n | gap_n | non_gap_n | gap_prevalence |
| --- | --- | --- | --- | --- |
| 2017 | 3599 | 736 | 2863 | 0.205 |
| 2018 | 3591 | 772 | 2819 | 0.215 |
| 2019 | 3611 | 640 | 2971 | 0.177 |
| 2020 | 3612 | 666 | 2946 | 0.184 |

Fold/split and target-year prevalence for all four definitions is in `reports/tables/a6_gap_target_summary.csv`; diagnostic threshold robustness by fold, year, and sector is in the corresponding `a6_gap_threshold_robustness*.csv` tables. Validation year changes are descriptive and not causal. The pandemic-year validation observations are 2020 only; there are no 2021 holdout summaries.

## Sector Distribution

| sector_code | eligible_n | gap_n | gap_prevalence | median_residual | median_threshold | median_residual_minus_threshold |
| --- | --- | --- | --- | --- | --- | --- |
| 11 | 125 | 50 | 0.400 | 0.535 | -1.470 | 2.005 |
| 21 | 208 | 123 | 0.591 | -1.692 | -1.470 | -0.222 |
| 22 | 292 | 2 | 0.007 | -0.167 | -1.470 | 1.303 |
| 23 | 1268 | 176 | 0.139 | 0.325 | -1.476 | 1.801 |
| 31-33 | 1001 | 178 | 0.178 | -0.226 | -1.476 | 1.250 |
| 42 | 627 | 110 | 0.175 | -0.420 | -1.470 | 1.050 |
| 44-45 | 1394 | 224 | 0.161 | -0.242 | -1.476 | 1.234 |
| 48-49 | 661 | 192 | 0.290 | 0.048 | -1.476 | 1.524 |
| 51 | 468 | 127 | 0.271 | 0.331 | -1.476 | 1.808 |
| 52 | 945 | 155 | 0.164 | -0.134 | -1.470 | 1.336 |
| 53 | 1045 | 220 | 0.211 | 0.509 | -1.476 | 1.985 |
| 54 | 846 | 175 | 0.207 | -0.154 | -1.470 | 1.315 |
| 55 | 357 | 9 | 0.025 | -0.075 | -1.470 | 1.395 |
| 56 | 907 | 206 | 0.227 | 0.001 | -1.476 | 1.477 |
| 61 | 437 | 140 | 0.320 | -0.402 | -1.476 | 1.074 |
| 62 | 858 | 110 | 0.128 | 0.078 | -1.476 | 1.555 |
| 71 | 708 | 209 | 0.295 | 0.115 | -1.470 | 1.585 |
| 72 | 1091 | 253 | 0.232 | -0.230 | -1.476 | 1.246 |
| 81 | 1175 | 155 | 0.132 | -0.032 | -1.476 | 1.444 |

Sector variation is not treated as a defect by itself; small sector samples and validation uncertainty matter. Cutoff-relative medians are supplied to aid reading.

## MSA Distribution

MSA prevalence is based on target-pair rows pooled across validation years and sectors. Only MSAs with at least 30 eligible validation observations are highlighted; this modest minimum screens sparse shares, not uncertainty-adjusted rankings. 258 MSAs meet the cutoff.

Lowest observed prevalence among qualifying MSAs:

| cbsa_code | eligible_n | gap_n | gap_prevalence |
| --- | --- | --- | --- |
| 40900 | 53 | 0 | 0 |
| 41740 | 68 | 0 | 0 |
| 41700 | 39 | 0 | 0 |
| 41620 | 51 | 0 | 0 |
| 18140 | 36 | 0 | 0 |

Highest observed prevalence among qualifying MSAs:

| cbsa_code | eligible_n | gap_n | gap_prevalence |
| --- | --- | --- | --- |
| 19500 | 30 | 17 | 0.567 |
| 33220 | 33 | 17 | 0.515 |
| 44300 | 50 | 24 | 0.480 |
| 16580 | 31 | 14 | 0.452 |
| 31700 | 64 | 28 | 0.438 |

The full MSA output includes all observed MSA groups, the minimum-N flag, and sample size. Extreme rates should not be read as stable rankings.

## Gap Persistence

Transitions use a consecutive prior calendar target year for the same MSA-sector and are summarized only when the current row is a validation target; the prior status uses the same fold-specific benchmark and cutoff. Missing intervening years are not bridged.

| fold | transition | transition_n | prior_target_year_min | target_year_min | target_year_max |
| --- | --- | --- | --- | --- | --- |
| fold_1 | gap_to_gap | 123 | 2016 | 2017 | 2017 |
| fold_1 | gap_to_non_gap | 475 | 2016 | 2017 | 2017 |
| fold_1 | non_gap_to_gap | 526 | 2016 | 2017 | 2017 |
| fold_1 | non_gap_to_non_gap | 2151 | 2016 | 2017 | 2017 |
| fold_2 | gap_to_gap | 126 | 2017 | 2018 | 2018 |
| fold_2 | gap_to_non_gap | 473 | 2017 | 2018 | 2018 |
| fold_2 | non_gap_to_gap | 574 | 2017 | 2018 | 2018 |
| fold_2 | non_gap_to_non_gap | 2134 | 2017 | 2018 | 2018 |
| fold_3 | gap_to_gap | 204 | 2018 | 2019 | 2020 |
| fold_3 | gap_to_non_gap | 1033 | 2018 | 2019 | 2020 |
| fold_3 | non_gap_to_gap | 937 | 2018 | 2019 | 2020 |
| fold_3 | non_gap_to_non_gap | 4469 | 2018 | 2019 | 2020 |

This is descriptive persistence, not a future predictor. Fold rows can share development history; they are not independent observations for inferential purposes.

## Comparison with A5 Descriptive Mismatch

A5 mismatch is reproduced exactly as high employment growth (at or above the full contemporaneous sector-year median) and low startup rate (below the corresponding median), with ties high. It is compared on the same validation target rows; the quadrant does not define or tune `gap_p20`.

| descriptive_mismatch | gap_p20 | n | share_of_formal_gaps | share_of_descriptive_mismatches |
| --- | --- | --- | --- | --- |
| 0 | 0 | 10021 |  |  |
| 0 | 1 | 1731 | 0.615 |  |
| 1 | 0 | 1578 |  | 0.593 |
| 1 | 1 | 1083 | 0.385 | 0.407 |

Formal gaps not captured by the descriptive mismatch: 1,731. Descriptive mismatches not classified as formal gaps: 1,578. Agreement is face-validity context only; disagreement is expected because one target is model-relative and the other is a contemporaneous median quadrant.

## Robustness Thresholds

| fold | split_role | threshold_definition | eligible_n | gap_n | gap_prevalence |
| --- | --- | --- | --- | --- | --- |
| fold_1 | training | p10 | 13955 | 1310 | 0.094 |
| fold_1 | validation | p10 | 3599 | 359 | 0.100 |
| fold_2 | training | p10 | 17554 | 1643 | 0.094 |
| fold_2 | validation | p10 | 3591 | 386 | 0.107 |
| fold_3 | training | p10 | 21145 | 1983 | 0.094 |
| fold_3 | validation | p10 | 7223 | 594 | 0.082 |
| fold_1 | training | p20 | 13955 | 2695 | 0.193 |
| fold_1 | validation | p20 | 3599 | 736 | 0.205 |
| fold_2 | training | p20 | 17554 | 3389 | 0.193 |
| fold_2 | validation | p20 | 3591 | 772 | 0.215 |
| fold_3 | training | p20 | 21145 | 4097 | 0.194 |
| fold_3 | validation | p20 | 7223 | 1306 | 0.181 |
| fold_1 | training | p25 | 13955 | 3385 | 0.243 |
| fold_1 | validation | p25 | 3599 | 931 | 0.259 |
| fold_2 | training | p25 | 17554 | 4251 | 0.242 |
| fold_2 | validation | p25 | 3591 | 943 | 0.263 |
| fold_3 | training | p25 | 21145 | 5138 | 0.243 |
| fold_3 | validation | p25 | 7223 | 1675 | 0.232 |
| fold_1 | training | mean_minus_1sd | 13955 | 1302 | 0.093 |
| fold_1 | validation | mean_minus_1sd | 3599 | 358 | 0.099 |
| fold_2 | training | mean_minus_1sd | 17554 | 1652 | 0.094 |
| fold_2 | validation | mean_minus_1sd | 3591 | 391 | 0.109 |
| fold_3 | training | mean_minus_1sd | 21145 | 2008 | 0.095 |
| fold_3 | validation | mean_minus_1sd | 7223 | 596 | 0.083 |

The p10, p20, p25, and mean-minus-SD rates, including target-year and sector breakouts, are retained in machine-readable tables. Primary status remains p20; natural prevalence is preserved.

## Gap Margin and Startup/Context Checks

`gap_margin = alignment_residual - primary_threshold`: negative is at/below the cutoff, zero is exactly at it, positive is above it. It is descriptive only and does not replace the binary outcome.

Observed startup rates among primary gaps versus non-gaps:

| gap_p20 | eligible_n | mean_startup_rate | median_startup_rate | p75_startup_rate | share_above_validation_median |
| --- | --- | --- | --- | --- | --- |
| 0 | 11599 | 7.251 | 7.143 | 9.288 | 0.581 |
| 1 | 2814 | 4.276 | 4.316 | 5.882 | 0.167 |

Primary gap observations above the pooled validation median observed startup rate: 470. This demonstrates that a gap is relative to expectation, not synonymous with a low absolute startup rate.

Gap prevalence by expected-rate tertile:

| expected_rate_group | eligible_n | gap_n | gap_prevalence | expected_rate_min | expected_rate_max |
| --- | --- | --- | --- | --- | --- |
| high | 4805 | 1094 | 0.228 | 7.772 | 21.698 |
| low | 4804 | 839 | 0.175 | -1.049 | 5.585 |
| middle | 4804 | 881 | 0.183 | 5.586 | 7.771 |

Gap prevalence by target-year employment-growth tercile:

| employment_growth_group | eligible_n | gap_n | gap_prevalence | employment_growth_min | employment_growth_max |
| --- | --- | --- | --- | --- | --- |
| high | 4805 | 853 | 0.178 | 0.021 | 2.452 |
| low | 4804 | 1001 | 0.208 | -0.560 | -0.015 |
| middle | 4804 | 960 | 0.200 | -0.015 | 0.021 |

## Negative Expected-Rate Audit

Negative expected startup rates are retained, not clipped.

| fold | split_role | n | negative_expected_n | negative_expected_share | negative_expected_gap_n |
| --- | --- | --- | --- | --- | --- |
| fold_1 | training_residual | 22450 | 365 | 0.016 | 0 |
| fold_1 | validation | 3599 | 32 | 0.009 | 0 |
| fold_2 | training_residual | 26337 | 426 | 0.016 | 0 |
| fold_2 | validation | 3591 | 49 | 0.014 | 0 |
| fold_3 | training_residual | 30230 | 478 | 0.016 | 0 |
| fold_3 | validation | 7223 | 107 | 0.015 | 0 |

Sector/year concentration appears in `a6_gap_negative_expected_by_year_sector.csv`. The p20 cutoff sensitivity excluding negative predictions is explicitly diagnostic only:

| fold | training_negative_expected_n | training_n | primary_p20 | p20_excluding_negative_expected | threshold_change | validation_label_flips |
| --- | --- | --- | --- | --- | --- | --- |
| fold_1 | 365 | 22450 | -1.470 | -1.495 | -0.025 | 14 |
| fold_2 | 426 | 26337 | -1.467 | -1.486 | -0.019 | 9 |
| fold_3 | 478 | 30230 | -1.476 | -1.499 | -0.023 | 22 |

Negative predictions are judged against both their share and gap overlap/threshold influence; no value is silently clipped or removed. If the alternate cutoff materially changes the target, the target should not advance without methodological review.

## Extreme Residual Audit

The most negative and most positive 15 validation residual observations are listed in `reports/tables/a6_gap_extreme_residuals.csv` with sector, year, observed/expected rates, and employment growth/denominator context where available. Fourteen of the 15 most negative have observed startup rate zero; none of either tail has a BDS suppression flag. None of the positive tail has zero observed startup rate. Prior-year employment denominators range as low as 80 in the negative tail and 78 in the positive tail, so small-market volatility is plausible and remains a caution. The records were retained rather than automatically deleted; one negative-tail and two positive-tail rows carry source-quality notes for follow-up.

## Complete-Case Selection Effects

Rows excluded from expected-rate target construction are exact t+3 key pairs missing one or more Model A response/predictor fields. Inclusion/exclusion summaries compare year, sector, observed startup rate, employment growth, ACS population, and CBP employment where available. These are descriptive mean/count comparisons and no imputation is performed. See `reports/tables/a6_gap_complete_case_selection.csv`.

Validation complete-case inclusion is about 89.8%-90.4% by fold. In all folds, excluded rows have lower mean observed startup rates (5.76-6.15 versus 6.58-6.72 among included rows) and much lower mean ACS populations (about 406,000-509,000 versus 798,000-807,000). This is material selection by market size and outcome level, not evidence that missingness is random. A6.3 therefore defines a target for the eligible complete-case subset; A6.4 must preserve and disclose that eligibility and must not imply representativeness of all MSAs or silently impute excluded observations.

## Leakage Safeguards and Holdout Preservation

- Each fold independently refits Model A through the frozen outcome cutoff.
- Thresholds use only that fold's training residuals; no validation residual enters cutoff estimation.
- Exact calendar `t+3` pairing requires the same CBSA and sector.
- Target-year benchmark fields appear only in the label artifact and are prohibited from future `X_t`.
- The target pair file contains no predictor-year feature matrix.
- Only development training/validation rows with target years through 2020 are emitted. No 2021-2023 holdout labels, prevalence, thresholds, or metrics were generated.
- The canonical SQLite analytical panel is read-only and unchanged.
- No Logistic Regression, Random Forest, Gradient Boosting/XGBoost, predictive PR-AUC, or classifier tuning was run.

The mechanical panel loader validates the source study range, after which the A6.3 runner restricts its working panel to target years at or before 2020 before creating pairs. Holdout outcomes are not summarized or written.

## Limitations and Readiness for A6.4

The target is suitable to advance to A6.4 for the explicitly defined complete-case population. The p20 cutoffs are negative and tightly grouped (-1.470 to -1.476), with natural pooled validation prevalence of 19.5% and nondegenerate variation across years, sectors, and MSAs. The formal target is not equivalent to A5's quadrant or simply low observed startup rates. Negative expected rates occur in roughly 0.9%-1.5% of validation rows, none is a p20 gap, and the diagnostic exclusion sensitivity flips fewer than 0.4% of validation labels per fold; no clipping is warranted. The important qualification is patterned complete-case selection: smaller markets and lower-startup observations are disproportionately excluded. A6.4 must retain this scope caveat and use only eligible target pairs. Training residuals are in-sample; validation fixed effects use the A6.2 carry-forward assumption; MSA/sector summaries are descriptive, not inferential. The final holdout remains untouched.

## Outputs

Thresholds: `reports/tables/a6_gap_thresholds_by_fold.csv`  
Development target pairs: `reports/tables/a6_gap_target_pairs.csv`  
Prevalence summary: `reports/tables/a6_gap_target_summary.csv`  
Specification: `docs/ASSIGNMENT6_GAP_TARGET.md`

- `reports/tables/a6_gap_complete_case_selection.csv`
- `reports/tables/a6_gap_descriptive_mismatch.csv`
- `reports/tables/a6_gap_employment_growth_groups.csv`
- `reports/tables/a6_gap_expected_rate_groups.csv`
- `reports/tables/a6_gap_extreme_residuals.csv`
- `reports/tables/a6_gap_negative_expected.csv`
- `reports/tables/a6_gap_negative_expected_by_year_sector.csv`
- `reports/tables/a6_gap_negative_expected_sensitivity.csv`
- `reports/tables/a6_gap_prevalence_by_msa.csv`
- `reports/tables/a6_gap_prevalence_by_sector.csv`
- `reports/tables/a6_gap_prevalence_by_year.csv`
- `reports/tables/a6_gap_startup_rate_comparison.csv`
- `reports/tables/a6_gap_target_pairs.csv`
- `reports/tables/a6_gap_target_summary.csv`
- `reports/tables/a6_gap_threshold_robustness.csv`
- `reports/tables/a6_gap_threshold_robustness_by_sector.csv`
- `reports/tables/a6_gap_threshold_robustness_by_year.csv`
- `reports/tables/a6_gap_thresholds_by_fold.csv`
- `reports/tables/a6_gap_transitions.csv`

- `reports/figures/a6_gap_thresholds_by_fold.png`
- `reports/figures/a6_gap_prevalence_by_year.png`
- `reports/figures/a6_gap_prevalence_by_sector.png`
- `reports/figures/a6_gap_residual_thresholds.png`
- `reports/figures/a6_gap_observed_startup_by_status.png`
- `reports/figures/a6_gap_by_expected_rate.png`
- `reports/figures/a6_gap_threshold_robustness.png`
- `reports/figures/a6_gap_vs_a5_mismatch.png`
- `reports/figures/a6_gap_transitions.png`
- `reports/figures/a6_gap_msa_prevalence_distribution.png`

Runner: `src/regional_entrepreneurship_intelligence/models/run_gap_target.py`; reusable target helpers: `src/regional_entrepreneurship_intelligence/models/gap.py`.
