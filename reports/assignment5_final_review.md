# Assignment 5 Final Review

## Assignment 5 Status

Complete for the documented exploratory-analysis scope. The repository has no separate course A5 rubric; the audit uses the proposal and A5 plan.

## Dataset

Final A4 metropolitan panel: 63,577 MSA-sector-year rows, 381 MSAs, 19 sectors, 2010-2023, and 5,887 panels (2,830 balanced; 3,057 unbalanced).

## Questions Addressed

Distributions and completeness; time, sector, and MSA variation; employment-growth/startup relationships; lag persistence; regional context; and descriptive growth-startup misalignment.

## Major Findings

Startup rate averages 6.42% (median 6.26%, 10.2% zeros). Employment growth is heavy-tailed; the pooled growth-startup association is weakly positive (Pearson 0.099, Spearman 0.193). All 19 sector correlations are positive but heterogeneous. Pooled startup lag-1 correlation is 0.690 versus 0.077 for within-panel demeaned persistence. The high-growth/low-startup descriptive quadrant is 19.29%, not a target.

## Data Quality Findings

Support missingness, structural lags, suppression, heavy tails, and small prior denominators are documented in A5.2. No destructive cleaning was applied.

## H1-H4 Preliminary Evidence

H1 predictive gain is untested; H2 has preliminary positive association evidence; H3 pooled persistence is not within-panel future-gap evidence; H4 has preliminary sector heterogeneity. None is accepted/rejected or proven.

## COVID-19 Context

Employment-growth median fell to -4.858% in 2020 and rebounded to 3.551% in 2021; startup medians were comparatively stable. No causal COVID effect was estimated.

## Robustness/Sensitivity

Excluding 2020-2021 leaves Pearson positive at 0.109; trimming employment-growth tails raises it from 0.099 to 0.155. Both are exploratory sensitivity analyses.

## Reproducibility

Run `uv run --offline python -m regional_entrepreneurship_intelligence.analysis.run_eda`. Two consecutive full runs regenerated identical artifacts in approximately 30 seconds per run; SHA-256 hashes matched for all 65 generated outputs (8 reports, 34 tables, 22 figures, and the A6 decision register). The analytical-panel fingerprint was identical before and after each workflow; no output accumulation occurred.

## Tests

`uv run --offline python -m unittest discover -s tests -v`: 65 passed, 0 failures, 0 errors, 0 skips. The pre-A5.5 baseline was 61 passing tests.

## Limitations

Available-case samples differ; annual growth has denominator sensitivity; MSA-sector coverage is unbalanced; pooled rows are dependent/repeated; descriptive associations do not establish causality or predictive validity.

## Assignment 6 Handoff

Target definition, residual alignment, three-year horizon, fold-safe target construction, baseline, metrics, year/sector treatment, tail handling, ACS grain, lags, correlated predictors, COVID sensitivity, and geographic holdout remain open in `docs/ASSIGNMENT6_MODELING_DECISIONS.md`. No target/model work has begun.
