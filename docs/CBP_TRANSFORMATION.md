# CBP Transformation

## Source Product

Assignment 4.10 uses the Census County Business Patterns API profiled in `docs/CBP_SOURCE_PROFILE.md`.

The A4.10 implementation transforms the committed official sample from:

```text
raw_cbp -> stg_cbp -> int_business_structure
```

It does not ingest new BDS, QCEW, or ACS data; integrate sources; build `analytics_msa_industry_year`; or create entrepreneurial-alignment or entrepreneurial-gap targets.

## Geography Strategy

A4.10 uses county-level CBP API rows and maps counties to the fixed July 2023 CBSA framework.

Implementation rule:

- preserve native CBP `state`, `county`, and derived `county_geoid` in `raw_cbp`
- classify counties present in `ref_geography_county_crosswalk` as `crosswalk_required`
- aggregate selected county records to `ref_geography.geography_id`
- retain unresolved geography records in quality/rejection metadata

The committed sample maps all source counties to CBSA `10180`, Abilene, TX.

## NAICS Comparability

CBP 2023 uses `NAICS2017` as the source industry field. A4.10 treats CBP source sectors as 2017 NAICS and the analytical reference as 2022 NAICS.

Classification statuses:

- `directly_comparable`: exact 2022 NAICS sector-level match, including combined sectors such as `31-33` and `44-45`
- `official_mapping_required`: reserved for future cases requiring an authoritative concordance
- `unresolved`: no direct analytical sector match

The sample source aggregate `00` is unresolved and does not advance to `int_business_structure`.

## Aggregation Method

Aggregation occurs after geography and industry checks.

Additive measures are summed across counties:

```text
establishments = sum(ESTAB)
employment = sum(EMP)
annual_payroll = sum(PAYANN)
first_quarter_payroll = sum(PAYQTR1)
```

CBP payroll values remain nominal and in thousands of dollars. No inflation adjustment is performed in A4.10.

## Suppression And Completeness

Suppressed, noisy, flagged, or missing county values are not converted to zero.

A4.10 uses a complete-case aggregation rule:

- staging keeps county-level rows with source flags and mapping statuses
- flagged rows are excluded from intermediate aggregation
- a CBSA-sector-year group advances only when all expected counties are observed and no component rows are flagged
- incomplete groups are recorded with reason code `incomplete_aggregation`

The committed sample has zero flagged rows. Sector `11` is intentionally incomplete for both years and is retained in staging but excluded from `int_business_structure`.

## Quality Controls

A4.10 records quality metrics for raw rows, staged rows, intermediate rows, mapping failures, flagged rows, incomplete aggregations, duplicate keys, MSA count, sector count, and year count.

Rejected-record reason codes used by the committed sample:

- `unresolved_industry`
- `incomplete_aggregation`

## Final Intermediate Grain

The final A4.10 intermediate grain is:

```text
geography_id x industry_id x year
```

Conceptually:

```text
MSA/CBSA x 2022 NAICS 2-digit sector x year
```

The A4.10 sample creates 6 intermediate rows for CBSA `10180`, sectors `23`, `31-33`, and `44-45`, and years 2022-2023.
