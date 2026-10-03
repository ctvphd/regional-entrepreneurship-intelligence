# ACS Transformation

## Scope

Assignment 4.9 moves ACS through:

```text
raw_acs -> stg_acs -> int_regional_controls
```

It does not ingest CBP, merge ACS with BDS or QCEW, build `analytics_msa_industry_year`, or create expected entrepreneurship, alignment residuals, or entrepreneurial-gap targets.

## Geography Standardization

ACS geography codes are preserved as source-native MSA/CBSA codes in `raw_acs`. A4.9 classifies each code against `ref_geography` using the fixed July 2023 CBSA reference.

Mapping statuses:

- `direct_match`: ACS code exists in the July 2023 CBSA reference
- `crosswalk_required`: reserved for future ACS geography cases requiring explicit mapping
- `unresolved`: code cannot be matched and is retained in staging/quality metadata

The committed sample has direct matches for all selected CBSAs.

## Variable Definitions

The selected ACS variables are:

- `DP05_0001E`: total population
- `DP03_0062E`: median household income
- `DP02_0068PE`: bachelor degree or higher among population 25 years and over
- `DP03_0002PE`: labor-force participation among population 16 years and over
- `DP03_0009PE`: unemployment rate among the civilian labor force

The corresponding ACS MOE variables are preserved in raw and staging.

## Percentage Calculations

A4.9 uses official ACS percentage estimates for education, labor-force participation, and unemployment. It does not manually construct percentages from numerator and denominator fields.

Percentages are validated to fall between 0 and 100.

## Population Growth

Population growth is calculated after MSA-year standardization:

```text
population_growth = (population_t - population_t_minus_1) / population_t_minus_1
```

Population growth is null when the prior calendar year is missing, suppressed, null, or nonpositive.

## Income Treatment

Median household income is kept as the source-reported ACS dollar estimate. A4.9 does not add a separate inflation series and does not label income as harmonized real dollars across years.

## Lags

A4.9 creates one-year lags only:

- `population_growth_lag1`
- `median_household_income_lag1`
- `educational_attainment_pct_lag1`
- `labor_force_participation_pct_lag1`
- `unemployment_rate_lag1`

Lag construction requires actual calendar continuity within the same MSA. Missing years are not forward-filled.

## Exclusions

Rows may be retained in staging but excluded from `int_regional_controls` for:

- `unresolved_geography`
- `missing_required_field`
- `invalid_numeric_value`
- `duplicate_standardized_key`

Ordinary first-year missing population growth is not a rejected record.

## Quality Checks

A4.9 records quality metrics for:

- raw rows
- staged rows
- intermediate rows
- unique MSAs
- year coverage
- geography mapping failures
- missing required values
- duplicate MSA-year keys
- invalid percentage values
- population-growth missingness
- lag missingness
- rejected rows

## Final Grain

The final A4.9 intermediate grain is:

```text
MSA/CBSA x year
```

ACS is intentionally not duplicated by industry in A4.9.

A4.11B's national registry-driven pass yielded 27,075 raw concept rows,
5,415 source MSA-year staging rows, and 5,194 complete regional-control rows
across 2010-2023. The 221 exclusions remain in staging and run-specific
rejection metadata; 700 raw concept rows have source CBSA codes absent from
the fixed July 2023 reference. A second run reproduced the same three table
counts. The 2019 education-ID shift is resolved by concept, not by reusing a
single variable ID across vintages.
