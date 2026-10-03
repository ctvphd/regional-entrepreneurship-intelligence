# Assignment 5.3: Time, Industry & MSA Pattern Analysis

## Executive Summary

The analysis covers 63,577 MSA-sector-year rows, 381 MSAs, 19 sectors, and 2010–2023. It is descriptive: no causal, predictive, or A5.4 relationship analysis is performed.

Sector medians span 55 (0) to 48-49 (9.03) for startup rate and 51 (-0.01333) to 71 (0.02981) for employment growth. 314 of 381 MSAs meet the documented coverage rule for comparative summaries.

## Time Patterns

Annual panel growth/startup summaries use available observations and report count, missingness, mean, median, standard deviation, and quartiles. ACS controls are summarized using one MSA-year row, not repeated industry rows. Growth rates are decimal changes; startup rates/profile percentages use percent units.

- `startup_rate` median: 5.668 in 2010 to 7.068 in 2023.
- `employment_growth` median: unavailable (no prior-year growth baseline) in 2010 to 0.01957 in 2023.
- `establishment_growth` median: unavailable (no prior-year growth baseline) in 2010 to 0.02569 in 2023.
- `payroll_growth` median: unavailable (no prior-year growth baseline) in 2010 to 0.05977 in 2023.

Employment growth is heavy-tailed, so the median is emphasized alongside the mean. Year tables report available counts and missing rates; ACS measures use MSA-year counts.

## 2020–2021 Descriptive Review

- `startup_rate` annual medians, 2019–2022: 2019 6.364, 2020 6.368, 2021 6.646, 2022 7.143
- `employment_growth` annual medians, 2019–2022: 2019 0.01246, 2020 -0.04858, 2021 0.03551, 2022 0.03853
- `establishment_growth` annual medians, 2019–2022: 2019 0.01515, 2020 0.01282, 2021 0.02219, 2022 0.03226
- `payroll_growth` annual medians, 2019–2022: 2019 0.04535, 2020 0.01408, 2021 0.09313, 2022 0.09337
- `unemployment_rate` annual medians, 2019–2022: 2019 5.2, 2020 5.2, 2021 5.2, 2022 5.1
- `acs_population_growth` annual medians, 2019–2022: 2019 0.004724, 2020 0.004874, 2021 0.009939, 2022 0.004048

These adjacent-year comparisons are descriptive only. No event-study, causal COVID attribution, or structural-break test was conducted.

## Industry Patterns

By sector median startup rate, the highest is 48-49 (9.03) and lowest is 55 (0); the highest and lowest median employment growth are 71 (0.02981) and 51 (-0.01333).

The largest/smallest startup-rate IQRs are 11 (11.93) and 55 (0); for employment growth they are 21 (0.1678) and 44-45 (0.0302). Employment-growth sector 95th percentiles are highest/lowest in 21 (0.344) / 44-45 (0.04883); 5th percentiles are highest/lowest in 21 (-0.3001) / 62 (-0.0388). IQR is the stated robust dispersion measure; standard deviation and MAD are also retained in tables. Dispersion is not performance.

Sector summaries include row/MSA/year counts, observed N, missingness, zero shares, quartiles, and tail-sensitive mean/standard deviation.

## Industry Volatility

Annual sector summaries are available by sector-year in `a5_sector_year_summary.csv`; volatility tables use IQR, standard deviation, and MAD.

## MSA Coverage

All 381 MSAs remain in the full summary. A comparison-eligible MSA must have at least 100 panel rows, 5 sectors, and 10 years; 314 qualify. The rule is an explicit coverage screen, not a quality judgment or statistical guarantee.

## MSA Entrepreneurship Patterns

Among eligible MSAs, the highest/lowest median startup rate is Las Vegas-Henderson-North Las Vegas, NV (11.52) / Lima, OH (3.061). The highest/lowest median employment growth is Wildwood-The Villages, FL (0.05925) / Johnstown, PA (-0.01087). Startup-rate IQR is largest in Eagle Pass, TX (10.11) and smallest in Minneapolis-St. Paul-Bloomington, MN-WI (2.303); the greatest startup zero share is Eagle Pass, TX (35.2%). Employment-growth IQR is greatest in Odessa, TX (0.138). These are descriptive orderings only.

## MSA Industry-Growth Patterns

Employment-growth medians and dispersion are summarized for every MSA. Means may be unstable under sparse support and heavy tails; eligibility limits, but does not eliminate, this concern. No observations are removed or winsorized.

## Regional Context

- `acs_population_growth`: lowest annual MSA median 0.003494 (2023); highest 0.009939 (2021); counts and missingness are in the year table.
- `median_household_income`: lowest annual MSA median 4.726e+04 (2010); highest 7.089e+04 (2023); counts and missingness are in the year table.
- `educational_attainment_pct`: lowest annual MSA median 24.4 (2010); highest 30.5 (2023); counts and missingness are in the year table.
- `labor_force_participation_pct`: lowest annual MSA median 62.1 (2018); highest 64.7 (2010); counts and missingness are in the year table.
- `unemployment_rate`: lowest annual MSA median 4.9 (2023); highest 9.4 (2013); counts and missingness are in the year table.

ACS controls are MSA-year measures repeated across industry rows in the integrated panel. Every ACS-only annual and MSA summary first validates within-MSA-year agreement and collapses to one row per MSA-year, preventing industry replication weighting. Income is not deflated to common-year dollars.

## Descriptive High-Growth / Low-Startup Patterns

Rows are classified against contemporaneous year-by-sector medians (ties count as high); 11,019 of 57,109 classified observations (19.29%) are high-growth/low-startup. The most frequent sectors are 44-45, 23, 31-33, 53, 81; the years with the largest shares are 2023, 2011, 2012. Among eligible MSAs, most frequent by count include Kalamazoo-Portage, MI (74), Reading, PA (67), Lancaster, PA (66), St. Cloud, MN (65), Amherst Town-Northampton, MA (65). `a5_descriptive_quadrants.csv` reports counts/percentages within sector-year; `a5_msa_descriptive_quadrants.csv` reports eligible-MSA frequencies and within-MSA shares. This exploratory grouping uses no future values and is NOT the final entrepreneurial-gap target, expected entrepreneurship, or a model label.

## Data Limitations

Growth missingness includes initial-year/prior-source availability constraints. Startup rate is a percentage; growth is decimal. ACS years and income definitions follow source release conventions. This panel is repeated across MSA-sector units; pooled summary counts are not independent samples.

## Questions Raised for Relationship Analysis

- Do sectors with higher employment growth also show different startup rates?
- Does startup-rate persistence vary by sector or MSA?
- How do population growth, unemployment, income, and education co-vary with the descriptive patterns?
- Are high-growth/low-startup observations more prevalent in particular sectors or years?
These questions are not tested here; they belong to A5.4.

## Figures

- `reports/figures/a5_time_startup_rate.png`
- `reports/figures/a5_time_employment_growth.png`
- `reports/figures/a5_time_unemployment.png`
- `reports/figures/a5_time_population_growth.png`
- `reports/figures/a5_sector_startup_rate.png`
- `reports/figures/a5_sector_employment_growth.png`
- `reports/figures/a5_sector_growth_volatility.png`
- `reports/figures/a5_msa_startup_distribution.png`
- `reports/figures/a5_msa_growth_distribution.png`
- `reports/figures/a5_descriptive_quadrant_prevalence.png`
