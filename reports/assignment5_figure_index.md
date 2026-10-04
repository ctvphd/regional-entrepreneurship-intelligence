# Assignment 5 Figure Index

Existing Assignment 5 figures reviewed for titles, axes, units, readability, and noncausal framing. Growth measures are decimal rates unless noted.

## `a5_startup_rate_histogram.png`
**Title:** Startup-rate distribution
**Step:** A5.2
**Interpretation:** The histogram shows the observed startup-rate distribution within its P01-P99 display window. The window omits tails for readability; the report tables retain full-range values.
**Caution:** Percent units; tail observations are outside the plotted window.

## `a5_employment_growth_histogram.png`
**Title:** Employment-growth distribution
**Step:** A5.2
**Interpretation:** The histogram displays the central P01-P99 range of annual employment growth. Extreme tails remain in the diagnostics and are not removed from the analytical data.
**Caution:** Growth is a decimal rate; the visible x-range is truncated to P01-P99.

## `a5_growth_boxplot.png`
**Title:** Growth-measure distributions
**Step:** A5.2
**Interpretation:** The boxplots compare central distributions across four annual growth measures. Fliers are hidden only to keep the boxes legible; this is not outlier deletion.
**Caution:** Rates are decimal values; fliers are visually hidden.

## `a5_missingness_summary.png`
**Title:** Missingness in selected measures
**Step:** A5.2
**Interpretation:** The bars compare missing-observation percentages for selected measures. Structural lags and source-support fields have different missingness mechanisms, detailed in the companion tables.
**Caution:** Percentages use the full analytical panel as denominator.

## `a5_time_startup_rate.png`
**Title:** Annual startup-rate median
**Step:** A5.3
**Interpretation:** The annual median varies modestly over the study window. Annual summaries are descriptive and do not identify causes of changes.
**Caution:** Percent units; aggregation is across observed MSA-sector rows.

## `a5_time_employment_growth.png`
**Title:** Annual employment-growth median
**Step:** A5.3
**Interpretation:** The annual median falls sharply in 2020 and rebounds in 2021. The pattern is descriptive and the underlying growth measure is heavy-tailed.
**Caution:** Decimal-rate units; medians summarize available MSA-sector observations.

## `a5_time_unemployment.png`
**Title:** Annual MSA unemployment median
**Step:** A5.3
**Interpretation:** This series summarizes unemployment at MSA-year grain across years. It describes context and is not a causal control estimate.
**Caution:** Percent units; each MSA-year contributes once.

## `a5_time_population_growth.png`
**Title:** Annual MSA population-growth median
**Step:** A5.3
**Interpretation:** The plot summarizes the annual distribution of population growth across MSAs. Extreme values and source coverage should be read with the tabular diagnostics.
**Caution:** Decimal-rate units; each MSA-year contributes once.

## `a5_sector_startup_rate.png`
**Title:** Startup-rate median by sector
**Step:** A5.3
**Interpretation:** Sector medians differ substantially, including a zero median in sector 55 and a high median in sectors 48-49. This is descriptive sector heterogeneity, not a ranking of performance.
**Caution:** Percent units; sector codes follow the project's NAICS reference.

## `a5_sector_employment_growth.png`
**Title:** Employment-growth median by sector
**Step:** A5.3
**Interpretation:** Sector medians range from negative growth in sector 51 to positive growth in sector 71. Heavy tails make these medians more representative of central outcomes than means alone.
**Caution:** Decimal-rate units; sector codes follow the project's NAICS reference.

## `a5_sector_growth_volatility.png`
**Title:** Sector employment-growth dispersion
**Step:** A5.3
**Interpretation:** The interquartile ranges show that central growth dispersion varies across sectors. The measure is descriptive and does not imply that sectors have comparable exposure or sample composition.
**Caution:** IQR of decimal growth rates; sector codes are retained.

## `a5_msa_startup_distribution.png`
**Title:** MSA median startup-rate distribution
**Step:** A5.3
**Interpretation:** The histogram shows variation in MSA median startup rates among MSAs meeting the comparison-coverage rule. It is not a best-to-worst ranking.
**Caution:** Percent units; restricted to eligible MSAs (at least 100 rows, 5 sectors, 10 years).

## `a5_msa_growth_distribution.png`
**Title:** MSA median employment-growth distribution
**Step:** A5.3
**Interpretation:** The histogram shows broad variation in MSA median employment growth among eligible MSAs. A small number of values extend into both tails.
**Caution:** Decimal-rate units; restricted to eligible MSAs.

## `a5_descriptive_quadrant_prevalence.png`
**Title:** High-growth / low-startup prevalence
**Step:** A5.3
**Interpretation:** The share varies over time under sector-year median cutoffs. This quadrant is a descriptive comparison only and is not the entrepreneurial-gap target.
**Caution:** Share of classified observations; cutoff-defined categories are not labels for modeling.

## `a5_relationship_growth_startup_scatter.png`
**Title:** Startup rate and employment growth
**Step:** A5.4
**Interpretation:** The pooled cloud shows a weak positive association amid substantial dispersion and a pronounced zero-startup mass. The plotted points are a reproducible subsample when the full panel exceeds the display cap.
**Caution:** Growth is decimal; startup rate is percent; association is not causal.

## `a5_relationship_growth_startup_binned.png`
**Title:** Binned median growth-startup pattern
**Step:** A5.4
**Interpretation:** Median startup rate generally rises across employment-growth bins, with irregularities in the tails. Binning is descriptive and cannot establish a functional or causal relationship.
**Caution:** Growth is decimal; startup rate is percent; bins use available cases.

## `a5_relationship_startup_lag1.png`
**Title:** Current and prior-year startup rates
**Step:** A5.4
**Interpretation:** Current and lagged rates have a strong pooled association that combines persistent differences between panels and within-panel change. It should not be interpreted as pure year-to-year momentum.
**Caution:** Both axes are percent; the plot does not isolate within-panel persistence.

## `a5_relationship_sector_correlations.png`
**Title:** Growth-startup correlation by sector
**Step:** A5.4
**Interpretation:** All 19 sector-specific Pearson correlations are positive but differ in magnitude. Estimates are exploratory and can vary with sample size and outliers.
**Caution:** Sector codes are NAICS; correlations are noncausal.

## `a5_relationship_correlation_matrix.png`
**Title:** Pooled Pearson correlation matrix
**Step:** A5.4
**Interpretation:** The matrix highlights related candidate measures, including employment and payroll growth and income and education. Pairwise samples can differ because of missingness; correlation alone does not determine model inclusion.
**Caution:** Pooled correlations; values are not adjusted for panel or time structure.

## `a5_relationship_startup_unemployment.png`
**Title:** Startup rate and unemployment
**Step:** A5.4
**Interpretation:** The scatter shows broad overlap and substantial dispersion between startup rate and unemployment. Each integrated row repeats an MSA-year unemployment value across sectors, so the companion regional summary uses MSA-year grain.
**Caution:** Unemployment and startup rate are percent; plotted pooled rows repeat ACS geography-year measures.

## `a5_relationship_startup_population_growth.png`
**Title:** Startup rate and population growth
**Step:** A5.4
**Interpretation:** The scatter shows substantial dispersion and a concentrated population-growth range. ACS population growth is measured at MSA-year grain and repeats across sector rows in the integrated panel.
**Caution:** Population growth is decimal; startup rate is percent; no causal interpretation.

## `a5_relationship_covid_sensitivity.png`
**Title:** Growth-startup correlation sensitivity
**Step:** A5.4
**Interpretation:** The pooled Pearson association remains positive when 2020 and 2021 are excluded. This sensitivity check does not estimate a COVID effect.
**Caution:** Correlation scale; excluded-year samples are sensitivity analyses.
