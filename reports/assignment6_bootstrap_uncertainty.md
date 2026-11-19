# Assignment 6.8B: Bootstrap Uncertainty for Holdout Average Precision

## Purpose

This post-assignment instructor-feedback remediation quantifies sampling uncertainty around the frozen final-holdout Average Precision values. It does not refit either model, alter probabilities, relabel outcomes, or change the evaluation sample.

## Bootstrap Design

A paired cluster bootstrap sampled the 365 observed MSAs with replacement and retained every holdout row belonging to each selected MSA. Repeatedly selected MSAs contributed repeated complete row clusters. Both models were evaluated on each identical resample. Seed `754` requested 5,000 replications; 5,000 were valid and 0 were excluded for containing only one target class.

The primary interval is the 2.5th-97.5th percentile interval. No BCa adjustment or row-level independence assumption is used. A target-year-stratified bootstrap was not added because resampling the same MSA separately within years would break its longitudinal cluster membership; the primary whole-MSA bootstrap preserves that dependence.

## Cluster Choice

The holdout contains 365 MSAs. Rows per MSA range from 1 to 56, with quartiles 18, 29, and 39; 1 MSA has one row. MSA clustering reflects shared economic and institutional conditions across sector-year rows within a metro.

## Holdout Sample

The unchanged artifact has 10,304 rows, 365 MSAs, target years 2021-2023, and prevalence 0.233. Logistic AP/prevalence is 1.74; HGB AP/prevalence is 1.82.

## Logistic AP Interval

Observed AP is 0.404225. Bootstrap mean is 0.404853, median 0.404832, SE 0.012433, and 95% percentile CI [0.380018, 0.429251].

## HGB AP Interval

Observed AP is 0.424238. Bootstrap mean is 0.424507, median 0.424820, SE 0.013305, and 95% percentile CI [0.397723, 0.449830].

## Paired Difference

Observed HGB minus Logistic AP is 0.020014. Bootstrap mean is 0.019654, median 0.019680, SE 0.007282, and 95% percentile CI [0.005531, 0.033684]. HGB exceeds Logistic in 99.7% of valid replications; Logistic exceeds HGB in 0.3%. The difference exceeds 0.01, 0.02, and 0.05 in 90.3%, 48.7%, and 0.0% of valid replications.

## Target-Year Context

- 2021: Logistic 0.435; HGB 0.449; N=3,372.
- 2022: Logistic 0.355; HGB 0.362; N=3,432.
- 2023: Logistic 0.427; HGB 0.462; N=3,500.

These are observed subgroup AP values, not separately bootstrapped estimates.

The frozen development comparison is less uniform: HGB exceeded Logistic in 2 of 3 temporal folds, and its pooled OOF AP gain was 0.004. No models were refit for this comparison.

## Model-Switch Rule

Replace Logistic only if the paired 95% MSA-cluster bootstrap CI for HGB minus Logistic AP is entirely above zero, the observed AP gain is at least 0.02, and the advantage is directionally stable across target years and existing robustness checks.

Rule components: CI entirely above zero = True; observed gain at least 0.02 = True; HGB directionally higher in every holdout target year = True; HGB higher in every development temporal fold = False. Overall rule met = False.

## Interpretation

The interval is entirely above zero, so the observed HGB advantage is distinguishable from zero under this bootstrap. Bootstrap proportions describe the empirical resampling distribution; they are not Bayesian posterior probabilities. The practical-size requirement and preselection discipline remain separate from statistical uncertainty.

## Limitations

The bootstrap treats observed MSAs as the resampling population, does not model future regime change, and does not repair complete-case selection or subgroup sparsity. Percentile intervals do not incorporate model-refitting uncertainty because predictions are intentionally frozen. There are only three target years, so temporal stability evidence remains limited.

## Effect on Primary-Model Decision

The prespecified switch rule is not met. Logistic remains the primary model pending student review because this remediation quantifies the frozen comparison and does not authorize a post-holdout model switch.

## Outputs

- `reports/tables/a6_holdout_ap_cluster_bootstrap.csv`
- `reports/figures/a6_holdout_ap_difference_bootstrap.png`
