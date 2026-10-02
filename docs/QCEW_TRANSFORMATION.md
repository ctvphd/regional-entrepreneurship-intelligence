# QCEW Transformation

## Source Product

Assignment 4.8 uses the BLS Quarterly Census of Employment and Wages (QCEW) NAICS-Based Annual CSV open-data family profiled in `docs/QCEW_SOURCE_PROFILE.md`.

The A4.8 implementation transforms the committed official sample from:

```text
raw_qcew -> stg_qcew -> int_industry_growth
```

It does not ingest ACS or CBP, integrate sources, build `analytics_msa_industry_year`, or create entrepreneurial-alignment or entrepreneurial-gap targets.

## Geography Strategy

A4.8 selects county-level aggregation to the fixed July 2023 CBSA framework.

Direct QCEW MSA records are not used as the primary transformation path because the project requires a fixed July 2023 analytical geography and the A4.7 profile did not establish that historical QCEW MSA area records are consistently aligned to that same vintage across 2010-2023. County FIPS identifiers provide a clearer bridge to the authoritative `ref_geography_county_crosswalk`.

Implementation rule:

- preserve native QCEW `area_fips` in `raw_qcew`
- classify county records present in `ref_geography_county_crosswalk` as `crosswalk_required`
- aggregate selected county records to `ref_geography.geography_id`
- retain unresolved geography records in quality/rejection metadata

The A4.7 sample counties map to CBSA `10180`, Abilene, TX.

## Ownership Decision

The main industry-growth panel uses private ownership only:

```text
own_code = 5
```

Excluded ownership categories remain in `raw_qcew` but do not advance to `stg_qcew` or `int_industry_growth`. This prevents double counting because total ownership rows already overlap ownership-specific rows.

Excluded rows are recorded with reason code `excluded_ownership`.

## NAICS Comparability

The analytical industry standard is 2022 NAICS at the 2-digit sector level.

QCEW source-native `industry_code` values are preserved in raw and staging. A4.8 classifies each source code as:

- `directly_comparable`: exact 2022 NAICS sector-level match, including combined sectors such as `31-33`, `44-45`, and `48-49`
- `official_mapping_required`: reserved for future source vintages where official concordance is needed
- `unresolved`: no direct 2022 sector-level match

A4.8 does not blanket-convert QCEW industry codes. Source code `10` and more detailed/non-sector status rows are unresolved for the 2-digit analytical sector panel.

## Aggregation Method

Aggregation occurs after geography, ownership, and industry checks.

Additive measures are summed across counties:

```text
employment = sum(annual_avg_emplvl)
establishments = sum(annual_avg_estabs)
total_annual_wages_nominal = sum(total_annual_wages)
```

Average annual pay is not averaged across counties. It is recalculated after aggregation:

```text
average_annual_pay_nominal = round(total_annual_wages_nominal / employment)
```

If employment is missing, suppressed, or nonpositive, average pay is null.

## Suppression Policy

Suppressed county values are not treated as zero.

A4.8 uses a complete-case aggregation rule:

- if any county component is suppressed, the aggregated row is retained in staging with suppression and incompleteness flags
- required numeric aggregate measures are set to null for incomplete/suppressed groups
- incomplete groups do not advance to `int_industry_growth`

Coverage indicators in `stg_qcew` and `int_industry_growth` include `counties_expected`, `counties_observed`, `counties_suppressed`, and `is_complete_county_coverage`.

## Annual Measures

The QCEW intermediate layer preserves nominal measures:

- `employment`
- `establishments`
- `total_annual_wages_nominal`
- `average_annual_pay_nominal`

No real-dollar conversion is performed in A4.8 because no inflation/deflator series has been added to the repository for this segment.

## Growth Formulas

Growth is calculated at the standardized `MSA x 2-digit sector x year` grain:

```text
growth_rate = (value_t - value_t_minus_1) / value_t_minus_1
```

A4.8 constructs `employment_growth`, `establishment_growth`, `payroll_growth`, and `wage_growth`. Growth is null when the prior calendar year is missing, the prior year is suppressed, the denominator is missing, or the denominator is zero or negative.

## Lag Formulas

Lags are constructed only after standardized growth rates exist in `int_industry_growth`.

A4.8 creates:

- `employment_growth_lag1`, `employment_growth_lag2`, `employment_growth_lag3`
- `establishment_growth_lag1`, `establishment_growth_lag2`, `establishment_growth_lag3`
- `payroll_growth_lag1`
- `average_pay_growth_lag1`

Calendar continuity is required: lag1 is `t - 1`, lag2 is `t - 2`, and lag3 is `t - 3`.

## Exclusions And Quality Controls

Rows can be retained in raw but excluded from staging or intermediate construction for `excluded_ownership`, `unresolved_geography`, `unresolved_industry`, `missing_required_measure`, or `incomplete_aggregation`. Ordinary first-year missing growth is not a rejected record.

A4.8 records quality metrics for raw rows, staged rows, intermediate rows, mapping failures, excluded ownership, suppressed rows, incomplete aggregations, missing growth, duplicate keys, lag missingness, valid panels, and year coverage.

## Final Intermediate Grain

The final A4.8 intermediate grain is:

```text
geography_id x industry_id x year
```

Conceptually:

```text
MSA/CBSA x 2022 NAICS 2-digit sector x year
```

The A4.8 sample creates 8 intermediate rows for CBSA `10180`, four directly comparable sectors, and years 2022-2023.
