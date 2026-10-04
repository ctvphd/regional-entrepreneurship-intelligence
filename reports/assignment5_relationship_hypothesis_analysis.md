# Assignment 5.4: Relationship & Hypothesis-Oriented Analysis

## Executive Summary

The primary pooled available-case association is r=0.099, N=57,109; Spearman is r=0.193, N=57,109. Sector correlations are positive in 19 and negative in 0 of 19 sectors, indicating pooled summaries may conceal heterogeneous patterns.

This is exploratory evidence, not causal inference, a final panel specification, prediction evaluation, or a formal test of the future-gap hypotheses. Pooled p-values assume independent observations and are not treated as inferential evidence here.

## H2 — Industry Growth and Entrepreneurship

Primary employment growth vs startup rate: Pearson r=0.099, N=57,109; Spearman r=0.193, N=57,109. Supporting Pearson correlations: establishment growth r=0.088, N=57,109, payroll growth r=0.077, N=57,109, wage growth r=0.014, N=57,109.

Regional controls in the correlation table use pairwise available observations. Pooled MSA-sector-year correlations repeat MSA-year ACS values across industries; the separately labeled MSA-year table instead correlates annual means across sectors with a single ACS record per MSA-year.

## H3 — Entrepreneurship Persistence

- Lag 1 pearson: r=0.690, N=54,894.
- Lag 1 spearman: r=0.722, N=54,894.
- Lag 2 pearson: r=0.657, N=50,599.
- Lag 2 spearman: r=0.704, N=50,599.
- Lag 3 pearson: r=0.648, N=46,406.
- Lag 3 spearman: r=0.702, N=46,406.
Within-panel demeaned lag-1 correlation: 0.077 (N=54,894); pooled-level result is 0.690.

These summarize persistence in observed startup rates only. They do NOT test whether prior entrepreneurship reduces future entrepreneurial-gap probability; no future gap outcome exists here.

## H4 — Sector Heterogeneity

Sector Pearson coefficients range from 55 (0.015, near zero) to 48-49 (0.212); all 19 are positive, with 2 near-zero (|r|<.05). The strongest coefficients are in sectors 48-49, 44-45, 23. Sector simple slopes range from 55 (0.142) to 44-45 (13.8) startup-rate points per unit growth rate. This variation is preliminary descriptive evidence of heterogeneity, not a confirmatory interaction test.

## Regional Context

Pooled startup-rate Pearson associations: population growth r=0.049, N=55,515; income r=0.157, N=60,039; education r=0.138, N=60,039; labor-force participation r=0.016, N=60,039; unemployment r=-0.047, N=60,039.

MSA-year-grain correlations, with industry-average startup/growth measures matched to one ACS record per geography-year:
- `acs_population_growth` vs MSA-year mean startup rate: Pearson r=0.101, N=4,653; Spearman r=0.480, N=4,653; vs MSA-year mean employment growth: Pearson r=0.030, N=4,643; Spearman r=0.246, N=4,643.
- `median_household_income` vs MSA-year mean startup rate: Pearson r=0.346, N=5,033; Spearman r=0.344, N=5,033; vs MSA-year mean employment growth: Pearson r=0.091, N=4,684; Spearman r=0.180, N=4,684.
- `educational_attainment_pct` vs MSA-year mean startup rate: Pearson r=0.315, N=5,033; Spearman r=0.358, N=5,033; vs MSA-year mean employment growth: Pearson r=0.065, N=4,684; Spearman r=0.130, N=4,684.
- `labor_force_participation_pct` vs MSA-year mean startup rate: Pearson r=0.072, N=5,033; Spearman r=0.126, N=5,033; vs MSA-year mean employment growth: Pearson r=0.009, N=4,684; Spearman r=0.036, N=4,684.
- `unemployment_rate` vs MSA-year mean startup rate: Pearson r=-0.103, N=5,033; Spearman r=-0.101, N=5,033; vs MSA-year mean employment growth: Pearson r=0.023, N=4,684; Spearman r=-0.044, N=4,684.

Pairwise candidate correlations are a redundancy screen, not an automatic variable-removal rule. Pooled Pearson employment-growth/payroll-growth is 0.714; payroll/wage growth is 0.621; income/education is 0.613; income/unemployment is -0.520. These are potentially overlapping signals, not proof that a predictor must be removed. No variable was dropped based on correlations or p-values.

## Exploratory Regression Results

- `bivariate`: N=57,109, R²=0.0098, growth coefficient=4.207 (SE 0.383; 95% CI 3.457 to 4.958; p <0.001).
- `regional_controls_year_sector`: N=53,655, R²=0.3675, growth coefficient=3.324 (SE 0.3; 95% CI 2.737 to 3.912; p <0.001).
- `sector_controls`: N=57,109, R²=0.3339, growth coefficient=3.532 (SE 0.282; 95% CI 2.979 to 4.085; p <0.001).
- `year_controls`: N=57,109, R²=0.0189, growth coefficient=4.241 (SE 0.414; 95% CI 3.43 to 5.052; p <0.001).
- `year_sector_controls`: N=57,109, R²=0.3420, growth coefficient=3.502 (SE 0.302; 95% CI 2.911 to 4.093; p <0.001).

Growth is stored as a decimal rate and startup rate as percentage points: the bivariate slope is per 1.0 (100 percentage point) growth-rate change; a 0.01 change corresponds to about 0.042 startup-rate points. The coefficient stays positive and declines from 4.207 pooled to 3.502 with year and sector controls; R² rises from 0.0098 to 0.342, largely reflecting sector/year level differences rather than a predictive-performance test. OLS covariance is clustered by MSA-industry panel. Even clustered standard errors do not address shared year shocks or all dependence structures. The year + sector model controls additive differences only; no interaction/final panel model is fit. The modest regional-controls specification is complete-case and its N may differ substantially.

## COVID-19 Context and Sensitivity

2020–2021 occurred during the COVID-19 pandemic and associated economic disruption and reopening. Excluding these years is sensitivity analysis, not a recommendation to delete them and not an estimate of a COVID effect.

- full: Pearson r=0.099 (N=57,109); Spearman r=0.193.
- exclude_2020: Pearson r=0.120 (N=52,739); Spearman r=0.218.
- exclude_2020_2021: Pearson r=0.109 (N=48,355); Spearman r=0.210.
The direction remains weakly positive in all samples; excluding 2020 alone changes magnitude more than excluding both years. This is sensitivity analysis only.

## Outlier Sensitivity

- full_pearson: r=0.099, N=57,109.
- full_spearman: r=0.193, N=57,109.
- exclude_employment_growth_p01_p99: r=0.155, N=55,965.
The P01/P99 specification excludes observations outside those employment-growth quantiles for this calculation only; production values are unchanged. The positive direction persists while Pearson magnitude increases after trimming (0.099 to 0.155), indicating tail observations affect magnitude but not sign. Spearman is a rank-based comparison, not an outlier deletion rule.

## Descriptive Quadrant Context

A5.3 sector-year median quadrant context, collapsed to one row per MSA-year within each quadrant: low_growth_high_startup: 4,237 MSA-year-quadrants (7.25% mean startup rate); high_growth_high_startup: 4,149 MSA-year-quadrants (7.54% mean startup rate); low_growth_low_startup: 3,982 MSA-year-quadrants (4.85% mean startup rate); high_growth_low_startup: 3,886 MSA-year-quadrants (4.98% mean startup rate). High-growth/low-startup versus high-growth/high-startup mean income is 56,267 vs 57,463, education 27.4% vs 28.3%, and unemployment 6.96% vs 7.02%. Selected ACS context means by quadrant are retained in `a5_quadrant_msa_year_context.csv`; each MSA-year contributes at most once to each quadrant. Among high-growth/low-startup observations, largest sector shares are 44-45, 23, 31-33 and largest year shares are 2023, 2011, 2012. Full sector/year composition counts are in `a5_quadrant_sector_composition.csv` and `a5_quadrant_year_composition.csv`.

`a5_quadrant_context.csv` summarizes classified MSA-sector-year rows; `a5_quadrant_msa_year_context.csv` collapses each MSA-year once within quadrant for regional context. These are descriptive group summaries, NOT the entrepreneurial-gap target and not regression outcomes.

## Multicollinearity / Predictor Redundancy

Pairwise matrix coefficients identify potentially redundant candidates but do not establish harmful multicollinearity in a final specification. Growth measures share economic content; income and education may co-vary; unemployment and labor-force participation may overlap. No VIF-based pruning or p-value selection was performed.

## Limitations

The primary pairwise available-case sample has N=57,109. The panel repeats MSA-industry observations over time, while ACS measures repeat across industries within MSA-year. Pooled observations and p-values are not independent/causal evidence. Extreme growth is heavy-tailed; all sensitivity filters are non-destructive. These analyses assess association and persistence, not predictive improvement or future outcomes.

## Implications for Assignment 6

Consider year and sector controls; compare candidate growth measures without collapsing them into an unvalidated index; assess panel-aware uncertainty; retain sensitivity checks for heavy tails; inspect lag availability/persistence; and handle ACS at its MSA-year origin grain. Correlated candidates merit specification diagnostics rather than automatic exclusion. No Assignment 6 code or target was created.

## Figures

- `reports/figures/a5_relationship_growth_startup_scatter.png`
- `reports/figures/a5_relationship_growth_startup_binned.png`
- `reports/figures/a5_relationship_startup_lag1.png`
- `reports/figures/a5_relationship_sector_correlations.png`
- `reports/figures/a5_relationship_correlation_matrix.png`
- `reports/figures/a5_relationship_startup_unemployment.png`
- `reports/figures/a5_relationship_startup_population_growth.png`
- `reports/figures/a5_relationship_covid_sensitivity.png`
