# Assignment 6.8C: Sector-Only Benchmark

## Purpose and design

This post-assignment benchmark asks how much frozen final-holdout ranking performance can be obtained from sector identity alone. Each sector receives its pooled development out-of-fold gap prevalence from `a6_baseline_oof_predictions.csv`. The mapping is then frozen and applied to the 2021-2023 holdout without reading holdout labels. No classifier was refit and no label, probability, row, or threshold was changed.

The development artifact contains 13,633 unique OOF evaluation rows through 2020. It is the committed leakage-safe development label population available for this benchmark; it is not a reconstruction of the final full-development fit. All 19 holdout sectors were observed in development, so no unseen-sector fallback was used.

## Final holdout comparison

| benchmark | AP | AP / prevalence | ROC-AUC | Brier | top-10% lift | 95% MSA-cluster AP CI |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Prevalence | 0.233 | 1.00 | 0.500 | 0.180 | 1.00 | not estimated |
| Sector-only | 0.325 | 1.40 | 0.617 | 0.174 | 1.80 | 0.299-0.352 |
| Logistic | 0.404 | 1.74 | 0.692 | 0.164 | 1.99 | 0.380-0.429 |
| HGB | 0.424 | 1.82 | 0.708 | 0.161 | 2.09 | 0.398-0.451 |

Sector-only AP is 0.325, compared with the no-information prevalence benchmark of 0.233. Logistic adds 0.079 AP over sector-only (24.3% relative), while HGB adds 0.099. Sector composition is therefore a meaningful benchmark, but the frozen models retain ranking information beyond sector identity.

Sector-only scores have only 19 distinct values. Top-decile lift is computed with the existing tie-aware boundary rule and should not be interpreted as precise within-sector prioritization.

## Paired MSA-cluster uncertainty

Seed `755` requested 5,000 paired replications over 365 whole MSA clusters; 5,000 were valid and 0 were excluded for containing one target class. Sector-only AP has a 95% percentile CI of 0.299-0.352.

The paired Logistic-minus-sector difference is 0.079, with CI [0.061, 0.098] and 100.0% of valid replications above zero. The HGB-minus-sector difference is 0.099, with CI [0.078, 0.121] and 100.0% above zero. Predictions remain frozen, so these intervals do not include refitting uncertainty.

## Within-sector Logistic ranking

Sector-only cannot rank two rows in the same sector. Logistic is therefore evaluated separately within sectors, using the existing minimum of 30 positive holdout labels. 17 of 19 sectors are eligible; 2 are suppressed. Among eligible sectors, median Logistic AP is 0.358, median natural prevalence is 0.259, median AP/prevalence is 1.50, and AP exceeds prevalence in 17 sectors. These subgroup estimates are descriptive and not separately bootstrapped.

## Sector prevalence drift

The rank correlation between development and holdout sector prevalence is 0.919. The largest increases are 42 (+0.126), 71 (+0.112), 11 (+0.096); the smallest changes are 54 (+0.006), 48-49 (-0.023), 56 (-0.025). This drift table is contextual evidence, not a recalibration step: holdout prevalence was never used to create sector scores.

## Relationship to Assignment 5

Assignment 5 R-squared describes how much variation the expected-startup regression explains in a continuous startup-rate outcome. Assignment 6 Average Precision evaluates ranking of a binary, fold-defined entrepreneurial-response gap. They answer different questions and should not be compared as if they shared a scale.

## Interpretation and limitations

Sector identity captures broad structural differences in gap prevalence, while the positive incremental AP results show that the frozen models rank risk beyond those broad sector rates. This is predictive association, not a causal sector effect. The comparison inherits complete-case selection, label-model dependence, 2-digit sector aggregation, only three holdout target years, and possible temporal regime change. Pooled development OOF labels are appropriate for a committed leakage-safe benchmark, but they are not identical to labels from a hypothetical single full-development refit.

## Outputs

- `reports/tables/a6_sector_only_model_comparison.csv`
- `reports/tables/a6_sector_prevalence_development_holdout.csv`
- `reports/tables/a6_sector_within_logistic_ranking.csv`
- `reports/figures/a6_sector_only_ap_comparison.png`
