# CBP Source Profile

## Source

Assignment 4.10 profiles the U.S. Census Bureau County Business Patterns (CBP) API.

Primary source family:

- Product: County Business Patterns API
- 2023 API documentation: `https://api.census.gov/data/2023/cbp.html`
- 2023 variable documentation: `https://api.census.gov/data/2023/cbp/variables.html`
- 2023 examples: `https://api.census.gov/data/2023/cbp/examples.html`
- Committed sample: `data/raw/cbp/sample/cbp_county_sector_sample_2022_2023.csv`
- Access method: official Census API

The committed sample covers selected Abilene-area Texas counties and selected source industries for 2022 and 2023. The full national CBP pull is not committed.

## Geography

Native geography fields:

- `state`
- `county`

A4.10 stores the combined state-plus-county GEOID as `source_county_geoid` and aggregates county rows to the fixed July 2023 CBSA framework through `ref_geography_county_crosswalk`.

The sample counties are:

- `48059`: Callahan County, Texas
- `48253`: Jones County, Texas
- `48441`: Taylor County, Texas

All three map to CBSA `10180`, Abilene, TX.

## Industry

Native industry field:

- `NAICS2017`

The analytical industry standard remains 2022 NAICS at the 2-digit sector level. A4.10 preserves CBP source-native 2017 NAICS sector codes in raw and staging, then allows only direct exact sector matches to advance to `int_business_structure`.

The source aggregate `00` is retained in raw/staging and rejected from the intermediate table as unresolved industry. No speculative NAICS concordance mapping is applied in A4.10.

## Measures

CBP measures preserved in the sample are:

- `ESTAB`: number of establishments
- `EMP`: number of employees
- `PAYANN`: annual payroll, in thousands of dollars
- `PAYQTR1`: first-quarter payroll, in thousands of dollars

Source flag fields are preserved for each measure. Suppressed, noisy, or flagged rows are not treated as zero.

## Raw Grain

The raw sample grain is:

```text
county x NAICS2017 sector x year x LFO x EMPSZES
```

A4.10 uses:

```text
LFO = 001
EMPSZES = 001
```

which correspond to the all-legal-forms and all-employment-size published totals used for the business-structure sample.

## A4.10 Resolution

A4.10 implements:

- `raw_cbp` source-native ingestion
- county-level `stg_cbp` standardization with geography and industry mapping statuses
- `int_business_structure` CBSA-sector-year aggregation for complete, unsuppressed, directly comparable groups
- rejected-record and quality-metric tracking for unresolved industry and incomplete county coverage

A4.10 does not merge CBP with BDS, QCEW, or ACS; does not build `analytics_msa_industry_year`; and does not create entrepreneurial-gap targets.
