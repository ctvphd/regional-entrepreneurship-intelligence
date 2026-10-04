# Assignment 6.2: Expected Entrepreneurship Model

**Decision:** Model A is the selected expected-rate specification for development. The final temporal holdout remains untouched. No A6.3 threshold or gap labels were created.

## Scope and leakage boundary

The startup-rate benchmark was estimated independently inside each A6.1 development fold using complete-case rows through the fold-specific outcome cutoff. Validation diagnostics use only exact same-MSA/same-sector t-to-t+3 pairs. Year and sector effects are fit only in training data. An unseen validation-year effect is carried forward from the latest training year; this forecasting convention uses no validation outcome. Validation outcome-year covariates and startup rates are confined to benchmark scoring/residual diagnostics and are not classifier features. No holdout rows from 2018-2020 predictors / 2021-2023 targets entered fitting or selection.

The data are not imputed, trimmed, or capped in the primary fits. Negative expected-rate predictions, if any, are retained and counted; rates are not post-hoc clipped. Robust and trimmed variants are sensitivities only.

## Panel and candidate comparison

| panel_rows | MSAs | sectors | year_min | year_max | development_folds | holdout_scored | gap_labels_created |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 63577 | 381 | 19 | 2010 | 2023 | 3 | False | False |

Fold-level raw eligibility before complete-case filtering:

| fold | fit_window_panel_rows | exact_validation_calendar_pairs |
| --- | --- | --- |
| fold_1 | 31630 | 4000 |
| fold_2 | 36152 | 3997 |
| fold_3 | 40691 | 7988 |

| fold | model | train_n | validation_n | train_mae | validation_mae | validation_rmse | validation_r_squared | validation_mean_residual | validation_residual_sd | validation_expected_below_zero_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fold_1 | A | 22450 | 3599 | 1.5481 | 1.4812 | 2.0342 | 0.6239 | -0.0723 | 2.0332 | 32 |
| fold_1 | B | 22450 | 3599 | 1.5410 | 1.4703 | 2.0227 | 0.6282 | -0.0560 | 2.0222 | 14 |
| fold_1 | C | 22450 | 3599 | 1.5162 | 1.4435 | 2.0274 | 0.6264 | -0.0468 | 2.0271 | 39 |
| fold_2 | A | 26337 | 3591 | 1.5424 | 1.5629 | 2.2244 | 0.5801 | -0.0089 | 2.2247 | 49 |
| fold_2 | B | 26337 | 3591 | 1.5349 | 1.5533 | 2.2164 | 0.5831 | -0.0143 | 2.2167 | 32 |
| fold_2 | C | 26337 | 3591 | 1.5115 | 1.5323 | 2.2379 | 0.5750 | 0.0494 | 2.2376 | 62 |
| fold_3 | A | 30230 | 7223 | 1.5516 | 1.5387 | 2.2819 | 0.5689 | 0.1316 | 2.2782 | 107 |
| fold_3 | B | 30230 | 7223 | 1.5434 | 1.5836 | 2.3250 | 0.5524 | 0.2552 | 2.3111 | 60 |
| fold_3 | C | 30230 | 7223 | 1.5202 | 1.5055 | 2.3024 | 0.5611 | 0.1745 | 2.2959 | 143 |

Selection: The linear baseline has the lower pooled development-fold MAE and is the parsimonious choice. Huber Model C reduced MAE in all three development folds (mean 1.494 versus 1.528 for Model A), but its mean RMSE was 2.189 and exceeded Model A in 2 of three folds; its later-fold positive residual drift also remained. It is retained as a typical-error robustness check, not selected as the primary benchmark because that MAE-only gain does not improve tail-sensitive error or temporal calibration consistently. Fold-level estimates and the exact feature/time specification are available in `reports/tables/a6_expected_model_comparison.csv` and `docs/ASSIGNMENT6_EXPECTED_MODEL.md`. R-squared is secondary: validation R-squared uses each fold's training-response mean as the reference, so negative values are possible and meaningful.

## Residual stability

The tables report validation residual summaries by outcome year, sector, and MSA. Group estimates should be interpreted alongside their sample sizes; MSA summaries are diagnostic rather than an additional selection target. Persistent year- or sector-level residual structure suggests that the conditional expectation is not fully calibrated, even where overall error is lower.

By year:

| model | group_value | n | mean_residual | median_residual | residual_sd | mae | rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 2017 | 3599 | -0.0723 | -0.1839 | 2.0332 | 1.4812 | 2.0342 |
| A | 2018 | 3591 | -0.0089 | -0.1097 | 2.2247 | 1.5629 | 2.2244 |
| A | 2019 | 3611 | 0.0762 | -0.0478 | 2.2722 | 1.5157 | 2.2732 |
| A | 2020 | 3612 | 0.1869 | 0.0725 | 2.2832 | 1.5618 | 2.2905 |
| B | 2017 | 3599 | -0.0560 | -0.1780 | 2.0222 | 1.4703 | 2.0227 |
| B | 2018 | 3591 | -0.0143 | -0.1056 | 2.2167 | 1.5533 | 2.2164 |
| B | 2019 | 3611 | 0.0856 | -0.0467 | 2.2620 | 1.5082 | 2.2633 |
| B | 2020 | 3612 | 0.4247 | 0.2817 | 2.3472 | 1.6589 | 2.3850 |
| C | 2017 | 3599 | -0.0468 | -0.1778 | 2.0271 | 1.4435 | 2.0274 |
| C | 2018 | 3591 | 0.0494 | -0.0518 | 2.2376 | 1.5323 | 2.2379 |
| C | 2019 | 3611 | 0.1411 | 0.0282 | 2.2878 | 1.4826 | 2.2918 |
| C | 2020 | 3612 | 0.2079 | 0.1042 | 2.3039 | 1.5284 | 2.3129 |

By sector:

| model | group_value | n | mean_residual | median_residual | residual_sd | mae | rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 11 | 125 | 0.9128 | 0.5347 | 6.6432 | 4.8718 | 6.6792 |
| A | 21 | 208 | -0.3432 | -1.6918 | 3.8922 | 2.5666 | 3.8980 |
| A | 22 | 292 | 0.0668 | -0.1667 | 2.2858 | 0.7361 | 2.2829 |
| A | 23 | 1268 | 0.4126 | 0.3251 | 1.8452 | 1.4332 | 1.8900 |
| A | 31-33 | 1001 | -0.1084 | -0.2263 | 1.6769 | 1.2524 | 1.6795 |
| A | 42 | 627 | -0.2584 | -0.4201 | 1.4749 | 1.1839 | 1.4962 |
| A | 44-45 | 1394 | -0.2031 | -0.2419 | 1.3163 | 1.0535 | 1.3314 |
| A | 48-49 | 661 | 0.1898 | 0.0483 | 3.1632 | 2.4216 | 3.1665 |
| A | 51 | 468 | 0.3110 | 0.3315 | 3.0146 | 2.3055 | 3.0274 |
| A | 52 | 945 | -0.0431 | -0.1338 | 1.6094 | 1.2353 | 1.6091 |
| A | 53 | 1045 | 0.4035 | 0.5085 | 2.3153 | 1.8437 | 2.3491 |
| A | 54 | 846 | -0.0804 | -0.1545 | 1.8324 | 1.4174 | 1.8331 |
| A | 55 | 357 | -0.0752 | -0.0749 | 0.7850 | 0.4762 | 0.7875 |
| A | 56 | 907 | 0.1035 | 0.0005 | 2.2745 | 1.7596 | 2.2756 |
| A | 61 | 437 | -0.0462 | -0.4024 | 3.9471 | 2.5667 | 3.9428 |
| A | 62 | 858 | 0.1500 | 0.0785 | 1.5789 | 1.1619 | 1.5851 |
| A | 71 | 708 | 0.1477 | 0.1146 | 3.1433 | 2.4154 | 3.1445 |
| A | 72 | 1091 | -0.2736 | -0.2302 | 1.7612 | 1.4034 | 1.7816 |
| A | 81 | 1175 | 0.0517 | -0.0318 | 1.4525 | 1.1226 | 1.4528 |
| B | 11 | 125 | 0.9059 | 0.5627 | 6.6457 | 4.8966 | 6.6808 |
| B | 21 | 208 | -0.3650 | -1.7621 | 3.8932 | 2.5852 | 3.9010 |
| B | 22 | 292 | 0.0432 | -0.1986 | 2.2735 | 0.7269 | 2.2700 |
| B | 23 | 1268 | 0.4238 | 0.3567 | 1.8346 | 1.4280 | 1.8822 |
| B | 31-33 | 1001 | -0.0925 | -0.2221 | 1.6818 | 1.2529 | 1.6835 |
| B | 42 | 627 | -0.2783 | -0.4283 | 1.4779 | 1.1934 | 1.5027 |
| B | 44-45 | 1394 | 0.0660 | 0.0227 | 1.3296 | 1.0463 | 1.3308 |
| B | 48-49 | 661 | 0.1878 | -0.0519 | 3.1010 | 2.3842 | 3.1044 |
| B | 51 | 468 | 0.3822 | 0.3585 | 3.0111 | 2.3034 | 3.0320 |
| B | 52 | 945 | -0.0509 | -0.1368 | 1.6126 | 1.2354 | 1.6126 |
| B | 53 | 1045 | 0.4173 | 0.5164 | 2.3146 | 1.8456 | 2.3509 |
| B | 54 | 846 | -0.0932 | -0.1722 | 1.8338 | 1.4204 | 1.8351 |
| B | 55 | 357 | -0.1130 | -0.1298 | 0.6748 | 0.3763 | 0.6832 |
| B | 56 | 907 | 0.0392 | -0.0546 | 2.2715 | 1.7603 | 2.2706 |
| B | 61 | 437 | -0.0789 | -0.4357 | 3.9475 | 2.5740 | 3.9438 |
| B | 62 | 858 | 0.1164 | 0.0336 | 1.5836 | 1.1664 | 1.5869 |
| B | 71 | 708 | -0.0084 | -0.0422 | 3.1331 | 2.4179 | 3.1309 |
| B | 72 | 1091 | 0.4124 | 0.2837 | 2.0915 | 1.6757 | 2.1309 |
| B | 81 | 1175 | 0.0521 | -0.0320 | 1.4578 | 1.1279 | 1.4581 |
| C | 11 | 125 | 1.9556 | 1.6172 | 6.7571 | 4.8030 | 7.0084 |
| C | 21 | 208 | 0.6067 | -0.5457 | 3.8377 | 1.9484 | 3.8762 |
| C | 22 | 292 | 0.1212 | -0.0634 | 2.2815 | 0.6451 | 2.2809 |
| C | 23 | 1268 | 0.3147 | 0.2219 | 1.8228 | 1.3819 | 1.8490 |
| C | 31-33 | 1001 | -0.0571 | -0.2224 | 1.6817 | 1.2385 | 1.6818 |
| C | 42 | 627 | -0.1673 | -0.3158 | 1.4652 | 1.1369 | 1.4736 |
| C | 44-45 | 1394 | -0.1753 | -0.1946 | 1.2894 | 1.0207 | 1.3008 |
| C | 48-49 | 661 | 0.2885 | 0.1256 | 3.1385 | 2.3924 | 3.1494 |
| C | 51 | 468 | 0.4190 | 0.3525 | 2.9698 | 2.2375 | 2.9961 |
| C | 52 | 945 | -0.0026 | -0.0577 | 1.6224 | 1.2308 | 1.6215 |
| C | 53 | 1045 | 0.3135 | 0.4118 | 2.3403 | 1.8271 | 2.3600 |
| C | 54 | 846 | -0.0393 | -0.0857 | 1.8235 | 1.3951 | 1.8229 |
| C | 55 | 357 | -0.0226 | -0.0194 | 0.7102 | 0.3997 | 0.7095 |
| C | 56 | 907 | 0.1201 | 0.0651 | 2.3084 | 1.7718 | 2.3102 |
| C | 61 | 437 | 0.2066 | -0.1186 | 4.0773 | 2.5515 | 4.0778 |
| C | 62 | 858 | 0.1895 | 0.1364 | 1.5721 | 1.1448 | 1.5826 |
| C | 71 | 708 | 0.0872 | 0.1006 | 3.1932 | 2.4260 | 3.1921 |
| C | 72 | 1091 | -0.2606 | -0.2341 | 1.7687 | 1.3953 | 1.7869 |
| C | 81 | 1175 | 0.0520 | -0.0279 | 1.4249 | 1.0912 | 1.4253 |

MSA-level results are retained in `reports/tables/a6_expected_residual_by_msa.csv` to keep this report readable. Coefficients and cross-fold stability are in `a6_expected_coefficients_by_fold.csv` and `a6_expected_coefficient_stability.csv`.

## Sensitivities

| fold | model | train_n | validation_n | train_mae | validation_mae | validation_rmse | validation_r_squared | validation_mean_residual |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fold_1 | A_without_lag1 | 24150 | 3764 | 1.9705 | 1.8953 | 2.6255 | 0.4333 | 0.0485 |
| fold_1 | A_lag2 | 18785 | 3590 | 1.5753 | 1.5515 | 2.2239 | 0.5516 | -0.0301 |
| fold_1 | A_lag3 | 15159 | 3764 | 1.5790 | 1.6101 | 2.3739 | 0.5336 | -0.0062 |
| fold_1 | A_establishment_growth | 22450 | 3599 | 1.5496 | 1.4859 | 2.0388 | 0.6222 | -0.0762 |
| fold_1 | A_payroll_growth | 22450 | 3599 | 1.5487 | 1.4886 | 2.0404 | 0.6216 | -0.0935 |
| fold_1 | A_wage_growth | 22450 | 3599 | 1.5501 | 1.4883 | 2.0422 | 0.6210 | -0.0728 |
| fold_1 | A_growth_p01_p99_trim | 22082 | 3599 | 1.5326 | 1.4835 | 2.0356 | 0.6230 | -0.0792 |
| fold_1 | A_msa_fixed_effects | 22450 | 3591 | 1.4285 | 1.3880 | 1.9663 | 0.6492 | -0.0549 |
| fold_2 | A_without_lag1 | 28297 | 3765 | 1.9726 | 1.9832 | 2.8693 | 0.3878 | -0.0064 |
| fold_2 | A_lag2 | 22644 | 3602 | 1.5779 | 1.6223 | 2.3638 | 0.5356 | -0.0935 |
| fold_2 | A_lag3 | 19026 | 3765 | 1.5865 | 1.7033 | 2.6464 | 0.4756 | -0.0450 |
| fold_2 | A_establishment_growth | 26337 | 3591 | 1.5439 | 1.5635 | 2.2271 | 0.5791 | -0.0040 |
| fold_2 | A_payroll_growth | 26337 | 3591 | 1.5431 | 1.5624 | 2.2241 | 0.5802 | -0.0042 |
| fold_2 | A_wage_growth | 26337 | 3591 | 1.5448 | 1.5676 | 2.2332 | 0.5768 | 0.0013 |
| fold_2 | A_growth_p01_p99_trim | 25907 | 3591 | 1.5270 | 1.5674 | 2.2287 | 0.5780 | -0.0180 |
| fold_2 | A_msa_fixed_effects | 26337 | 3591 | 1.4242 | 1.4589 | 2.0941 | 0.6278 | 0.0139 |
| fold_3 | A_without_lag1 | 32482 | 7556 | 1.9874 | 1.9466 | 2.7795 | 0.4157 | 0.1339 |
| fold_3 | A_lag2 | 26555 | 7213 | 1.5914 | 1.5802 | 2.3814 | 0.5448 | 0.1653 |
| fold_3 | A_lag3 | 22917 | 7556 | 1.6070 | 1.6539 | 2.5072 | 0.5210 | 0.0286 |
| fold_3 | A_establishment_growth | 30230 | 7223 | 1.5527 | 1.5386 | 2.2822 | 0.5688 | 0.0316 |
| fold_3 | A_payroll_growth | 30230 | 7223 | 1.5521 | 1.5365 | 2.2813 | 0.5691 | 0.0770 |
| fold_3 | A_wage_growth | 30230 | 7223 | 1.5540 | 1.5419 | 2.2876 | 0.5667 | 0.0324 |
| fold_3 | A_growth_p01_p99_trim | 29730 | 7223 | 1.5363 | 1.5600 | 2.3032 | 0.5603 | 0.2415 |
| fold_3 | A_msa_fixed_effects | 30230 | 7180 | 1.4348 | 1.4330 | 2.1543 | 0.6165 | 0.1421 |

Sensitivity changes are one-at-a-time: remove lag 1; substitute lag 2 or lag 3; substitute establishment, payroll, or wage growth for employment growth; temporarily trim training employment growth at training-only P01/P99; or add MSA fixed effects. The trim cutoffs are learned only in each training fold, and validation data remain untrimmed. The MSA-FE result is diagnostic and does not change the primary policy against MSA effects. Huber Model C, included in the primary comparison, checks sensitivity to large residuals while preserving all observations.

All development training windows end by 2018, so COVID years 2020-2021 do not enter fold fits. The year-2020 validation residual is reported separately from 2019. A pre-holdout in-sample fit sensitivity also compares retaining 2020 with excluding 2020 and 2020-2021; 2021 is outside the permitted pre-holdout training window, so the latter two fitting samples are intentionally identical. These are descriptive robustness checks, not causal COVID estimates. No final-holdout observations enter them.

## Interpretation and next step

Residual = observed startup rate minus expected startup rate. Positive residuals are above expectation and negative residuals are below expectation; a negative residual alone is not a gap. Coefficients are conditional associations, not causal effects. The preferred model will be used in A6.3 only after the leakage and calibration diagnostics are reviewed; A6.3 must calculate residual thresholds from training-fold residuals only.

## Figures

- `reports/figures/a6_expected_observed_vs_expected.png`
- `reports/figures/a6_expected_residual_distributions.png`
- `reports/figures/a6_expected_validation_mae.png`
- `reports/figures/a6_expected_validation_rmse.png`
- `reports/figures/a6_expected_residual_by_year.png`
- `reports/figures/a6_expected_residual_by_sector.png`
- `reports/figures/a6_expected_residual_vs_fitted.png`
- `reports/figures/a6_expected_residual_dispersion.png`

## Machine-readable outputs

- `reports/tables/a6_expected_model_comparison.csv`
- `reports/tables/a6_expected_residual_by_year.csv`
- `reports/tables/a6_expected_residual_by_sector.csv`
- `reports/tables/a6_expected_residual_by_msa.csv`
- `reports/tables/a6_expected_coefficients_by_fold.csv`
- `reports/tables/a6_expected_coefficient_stability.csv`
- `reports/tables/a6_expected_sensitivity.csv`
- `reports/tables/a6_expected_validation_predictions.csv`
