# BDS Source Profile

## Source

Assignment 4.5 profiles the U.S. Census Bureau Business Dynamics Statistics (BDS) 2023 release.

Primary official product for A4.5 raw ingestion:

- Product: Business Dynamics Statistics: MSA by Sector
- Bulk file: `bds2023_msa_sec.csv`
- Official URL: `https://www2.census.gov/programs-surveys/bds/tables/time-series/2023/bds2023_msa_sec.csv`
- Local permitted sample: `data/raw/bds/sample/bds2023_msa_sec_sample_2010_2023.csv`
- Access method: official Census bulk CSV
- Release/version: 2023 BDS release, 1978-2023 time series

The official Census BDS API was reviewed. It requires a Census API key for data calls, while the bulk CSV is directly reproducible and contains the needed MSA by sector by year panel. Therefore A4.5 uses the bulk source family and commits only a small permitted sample because the full `MSA by Sector` file is about 90MB and the richer `MSA by Sector by Firm Age Coarse` file is about 405MB.

## Geography

Native geography field:

- `msa`

Native geography level:

- Metropolitan/micropolitan statistical area code in the BDS bulk `MSA by Sector` file.

Documented vintage/definition:

- The BDS API documentation identifies `metropolitan statistical area/micropolitan statistical area` as a supported geography and uses CBSA-style codes.
- A4.5 did not find enough source documentation in the file itself to prove that BDS records are already recast to the project's July 2023 CBSA delineation standard.

Mapping issue to July 2023 CBSA:

- Do not join raw `msa` directly to `ref_geography` as if vintage compatibility were proven.
- A4.6 must verify the BDS MSA vintage/crosswalk behavior and decide whether direct CBSA code matching is valid or whether a historical geography crosswalk is required.

## Industry

Native industry field:

- `sector`

Available level:

- NAICS sector-level categories in the profiled `MSA by Sector` bulk file.
- Official combined sector codes appear, including values such as `31-33` and `44-45`.

Documented NAICS vintage:

- BDS documentation and API metadata identify NAICS sector, 3-digit, and 4-digit industry support, but A4.5 does not prove that every 2010-2023 source row is already harmonized to the project's 2022 NAICS analytical standard.

Mapping issue to 2022 NAICS:

- Do not map `sector` to `ref_industry` speculatively in raw ingestion.
- A4.6 must verify BDS NAICS vintage handling and decide how to use the preserved 2012/2017/2022 NAICS concordance files.

## Measures

The `bds2023_msa_sec.csv` source includes source-native measures such as:

- `firms`
- `estabs`
- `emp`
- `denom`
- `estabs_entry`
- `estabs_entry_rate`
- `estabs_exit`
- `estabs_exit_rate`
- `job_creation`
- `job_creation_births`
- `job_creation_continuers`
- `job_creation_rate_births`
- `job_creation_rate`
- `job_destruction`
- `job_destruction_deaths`
- `job_destruction_continuers`
- `net_job_creation`
- `firmdeath_firms`
- `firmdeath_estabs`
- `firmdeath_emp`

A4.5 loads these values as source-native raw payloads. It does not calculate startup rates, lagged startup rates, standardized measures, or final analytical targets.

## Suppression

The Census API documentation states that BDS indicator flags can be `D`, `N`, `S`, or `X`:

- `D`: suppressed due to too few firms
- `N`: rate cannot be calculated
- `S`: suppressed due to data quality concerns
- `X`: unavailable due to structural missingness

The BDS bulk sample stores these status values directly in measure columns. A4.5 preserves them in `raw_payload` and sets `is_suppressed = 1` when a row contains `D` or `S`. Numeric source values are not silently coerced to zero.

## Time Coverage

Source coverage:

- BDS 2023 release time series covers 1978-2023.

Usable A4.5 sample coverage:

- 2010-2023, matching the project study window.

The sample is intentionally not presented as the full BDS source. It exists to exercise raw ingestion and validation without committing the full national file.

## Grain

Raw BDS sample grain:

```text
year x msa x sector
```

The full official `MSA by Sector` file has the same profiled grain. The richer `MSA by Sector by Firm Age Coarse` file adds `fagecoarse` and can support explicit age-zero startup concepts later, but it is substantially larger and should be handled with the safe raw-data policy.

## A4.6 Mapping Requirements

Before BDS can become `stg_bds`, A4.6 must:

- verify whether BDS `msa` codes are compatible with the July 2023 CBSA delineation or require historical crosswalking
- verify BDS sector/NAICS vintage handling for 2010-2023
- decide how combined sector codes map to `ref_industry`
- choose whether the MSA-by-sector file is sufficient or whether the MSA-by-sector-by-firm-age-coarse file is required for firm-startup concepts
- preserve `D`, `N`, `S`, and `X` status semantics during staging
- avoid calculating lag variables until the later lag framework step

## Startup Measure Construction

A4.6 uses the BDS MSA by Sector by Firm Age Coarse source for the primary startup concept.

- Source table: `bds2023_msa_sec_fac.csv`
- Firm age category: `a) 0`
- Numerator: `firms` from age-0 rows
- Denominator: `firms` from the BDS MSA by Sector backbone for the same MSA-sector-year
- Resulting measure: `startup_rate = age_0_firms / all_firms * 100`

This measure is appropriate because Census defines startups as firms with age 0. When the numerator or denominator is suppressed, unavailable, nonnumeric, or zero, the startup rate is left null. Establishment entry and establishment entry rate are retained as supporting measures, not as the primary startup definition.

## Lag Construction

A4.6 creates `startup_rate_lag1`, `startup_rate_lag2`, and `startup_rate_lag3` only after BDS records are standardized to internal geography and industry identifiers.

Lag grouping keys:

- `geography_id`
- `industry_id`

Calendar-year continuity rule:

- lag1 requires year `t - 1`
- lag2 requires year `t - 2`
- lag3 requires year `t - 3`

If a calendar year is missing, the corresponding lag is null. Lags are not forward-filled, and suppressed prior values are not used as valid lag values.

## A4.11 National Acquisition

The official 2023 release files were downloaded to ignored
`data/raw/bds/production/`. The full MSA-sector file has 808,450 rows and
89,784,307 bytes; the full MSA-sector-firm-age-coarse file has 4,042,250 rows
and 404,097,490 bytes. The study-window extracts retain 246,050 backbone rows
and 246,050 age-0 firm rows across 2010-2023. Original-file and extract
checksums are separately recorded in the production SQLite manifest. The
production command is documented in the quality report.
