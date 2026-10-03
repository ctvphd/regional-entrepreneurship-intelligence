# Table Registry

This registry defines the Assignment 4 SQLite schema. It documents the planned table grain, layer, keys, business rule, and current population status for every implemented table. Raw tables are intentionally flexible and source-faithful; standardized reference, staging, intermediate, analytics, metadata, and quality tables are normalized where practical.

Assignment 4.3 populated only verified deterministic reference records: `ref_year` contains the 14 primary study years from 2010 through 2023, and `ref_source` contains the four approved source systems. Assignment 4.4 adds authoritative geography and NAICS reference loading from official Census assets. No geography or industry rows are manually fabricated.

| Table | Layer | Grain | PK | Main FKs | Source | Materialized? | Committed or generated | Purpose |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ref_geography` | Reference | One standardized geography record per CBSA/source vintage | `geography_id` | None | Census CBSA delineation List 1 | Yes | Generated and loaded in SQLite | Stores July 2023 CBSA metropolitan and micropolitan geography references. |
| `ref_geography_county_crosswalk` | Reference | One county membership row per CBSA x county x source vintage | `county_crosswalk_id` | `geography_id` -> `ref_geography` | Census CBSA delineation List 1 | Yes | Generated and loaded in SQLite | Preserves county-to-CBSA membership for later QCEW/CBP county aggregation and validation. |
| `ref_industry` | Reference | One NAICS record per NAICS code/version | `industry_id` | None | Census NAICS structure file | Yes | Generated and loaded in SQLite | Stores 2022 NAICS hierarchy, including official combined two-digit sectors. |
| `ref_year` | Reference | One row per calendar year | `year` | None | Deterministic reference | Yes | Generated and seeded in SQLite | Identifies the 2010-2023 primary study years; A4.3 seeds exactly 14 rows. |
| `ref_source` | Reference | One row per source registry entry | `source_id` | None | Project metadata | Yes | Generated and seeded in SQLite | Registers the four approved planned source datasets and agencies. |
| `metadata_source_manifest` | Metadata | One row per retrieved source file or API result | `manifest_id` | `source_id` -> `ref_source` | Pipeline metadata | Yes | Generated in SQLite | Records provenance, access method, source version, raw filename, checksum, and row count. |
| `metadata_pipeline_run` | Metadata | One row per pipeline stage run | `pipeline_run_id` | None | Pipeline metadata | Yes | Generated in SQLite | Records run status, timing, stage, counts, warnings, and errors. |
| `raw_bds` | Raw | One source-native BDS MSA-sector row | `raw_bds_id` | `manifest_id`, `pipeline_run_id` | BDS | Yes | Generated in SQLite; sample-loaded in A4.5 | Preserves source-native BDS MSA, sector, year, status values, and raw payload without standardizing geography or NAICS. |
| `raw_bds_firm_age` | Raw | One source-native BDS MSA-sector-firm-age row | `raw_bds_firm_age_id` | `manifest_id`, `pipeline_run_id` | BDS | Yes | Generated in SQLite; sample-loaded in A4.6 | Preserves source-native BDS firm-age-coarse rows used for age-0 startup construction. |
| `raw_qcew` | Raw | One source-native QCEW annual area row | `raw_qcew_id` | `manifest_id`, `pipeline_run_id` | QCEW | Yes | Generated in SQLite; sample-loaded in A4.7 | Preserves source-native QCEW area, ownership, industry, size, annual measures, disclosure codes, and raw payload without standardizing geography or NAICS. |
| `raw_cbp` | Raw | One source-native CBP county-sector-year row | `raw_cbp_id` | `manifest_id`, `pipeline_run_id` | CBP | Yes | Generated in SQLite; sample-loaded in A4.10 | Preserves source-native CBP county, 2017 NAICS sector, legal-form, employment-size, measure, flag, and raw payload fields. |
| `raw_acs` | Raw | One ACS estimate/MOE variable row per source geography-year | `raw_acs_id` | `manifest_id`, `pipeline_run_id` | ACS | Yes | Generated in SQLite; sample-loaded in A4.9 | Preserves source-native ACS geography, variable IDs, estimates, MOEs, product metadata, request URL, and raw payload. |
| `stg_bds` | Staging | BDS MSA x sector x year x firm-age-derived startup row | `stg_bds_id` | `raw_bds_id`, `manifest_id`, `pipeline_run_id`, `geography_id`, `industry_id`, `year` | BDS | Yes | Generated in SQLite by A4.6 | Standardizes BDS age-0 startup fields while retaining source-native codes, mapping statuses, and missing/suppression flags. |
| `stg_qcew` | Staging | Aggregated QCEW CBSA-sector-year row | `stg_qcew_id` | `raw_qcew_id`, `manifest_id`, `pipeline_run_id`, `geography_id`, `industry_id`, `year` | QCEW | Yes | Generated in SQLite by A4.8 | Standardizes private-sector QCEW county rows to July 2023 CBSA-sector-year geography with coverage and suppression indicators. |
| `stg_cbp` | Staging | County x source sector x year row with mapping statuses | `stg_cbp_id` | `raw_cbp_id`, `manifest_id`, `pipeline_run_id`, `geography_id`, `industry_id`, `year` | CBP | Yes | Generated in SQLite by A4.10 | Preserves CBP county-level rows while adding July 2023 CBSA mapping status, 2022 sector comparability status, measures, and source flags. |
| `stg_acs` | Staging | MSA x year | `stg_acs_id` | `raw_acs_id`, `manifest_id`, `pipeline_run_id`, `geography_id`, `year` | ACS | Yes | Generated in SQLite by A4.9 | Standardizes ACS regional control fields and MOEs for MSA-year joins without adding industry identifiers. |
| `int_entrepreneurship` | Intermediate | Standardized MSA x directly comparable sector x year | `(geography_id, industry_id, year)` | `geography_id`, `industry_id`, `year`, `source_manifest_id`, `pipeline_run_id` | BDS-derived | Yes | Generated in SQLite by A4.6 | Holds standardized BDS entrepreneurship measures and startup-rate lags without final gap targets. |
| `int_industry_growth` | Intermediate | MSA x 2-digit NAICS x year | `(geography_id, industry_id, year)` | `geography_id`, `industry_id`, `year`, `source_manifest_id`, `pipeline_run_id` | QCEW-derived | Yes | Generated in SQLite by A4.8 | Holds nominal QCEW industry levels, growth measures, selected growth lags, coverage flags, and nominal/real-adjustment flag. |
| `int_regional_controls` | Intermediate | MSA x year | `(geography_id, year)` | `geography_id`, `year`, `source_manifest_id`, `pipeline_run_id` | ACS-derived | Yes | Generated in SQLite by A4.9 | Holds ACS regional controls, population growth, and selected one-year regional-control lags. |
| `int_business_structure` | Intermediate | MSA x 2-digit NAICS x year | `(geography_id, industry_id, year)` | `geography_id`, `industry_id`, `year`, `source_manifest_id`, `pipeline_run_id` | CBP-derived | Yes | Generated in SQLite by A4.10 | Holds complete-coverage CBP business-structure measures used for validation/context. |
| `analytics_msa_industry_year` | Analytics | MSA x 2-digit NAICS x year | `(geography_id, industry_id, year)` | `geography_id`, `industry_id`, `year`, `pipeline_run_id` | Integrated analytical panel | Yes | Generated in SQLite | Canonical clean analytical table. It intentionally excludes global expected entrepreneurship, residual alignment, and final gap target fields. |
| `quality_rejected_record` | Quality | One rejected or explicitly reviewed record | `rejection_id` | `pipeline_run_id`, `source_id` | Pipeline quality | Yes | Generated in SQLite | Records bad-record handling and reason codes without silently discarding records. |
| `quality_table_metric` | Quality | One quality metric per table/run/scope | `metric_id` | `pipeline_run_id` | Pipeline quality | Yes | Generated in SQLite | Supports row counts, missingness, duplicates, rejected records, and merge-rate metrics. |

## Model-Ready Layer

No physical model-ready table is materialized in A4.2. The model-ready layer belongs primarily to Assignments 5-6, where fold-specific targets and leakage-safe derived outcomes can be created within temporal training logic.

## A4.3 Seeded Source Registry

The `src/regional_entrepreneurship_intelligence/database/reference.py` helper seeds the following `ref_source` records only:

- Census Business Dynamics Statistics (BDS)
- BLS Quarterly Census of Employment and Wages (QCEW)
- Census County Business Patterns (CBP)
- American Community Survey (ACS)

Endpoint and homepage fields are intentionally left null until source-specific ingestion verifies the exact official access path used by the pipeline.

## A4.4 Authoritative Reference Assets

Reference assets are stored under `data/external/reference/` with official filenames preserved:

- `list1_2023.xlsx`: Census July 2023 CBSA delineation List 1
- `2022_NAICS_Structure.xlsx`: Census 2022 NAICS Structure with Change Indicator
- `2022_to_2017_NAICS.xlsx`, `2017_to_2022_NAICS.xlsx`, `2017_to_2012_NAICS.xlsx`, `2012_to_2017_NAICS.xlsx`: Census NAICS concordance assets preserved for later source-specific mapping

The A4.4 loader records these files in `metadata_source_manifest` with official URLs, checksums, row counts, source versions, and notes. It loads `ref_geography`, `ref_geography_county_crosswalk`, and `ref_industry`; it does not ingest BDS, QCEW, CBP, or ACS observations.

## A4.5 BDS Raw Ingestion

Assignment 4.5 profiles the official Census BDS source family and implements source-native raw ingestion for a permitted sample:

- Source profile: `docs/BDS_SOURCE_PROFILE.md`
- Loader: `src/regional_entrepreneurship_intelligence/etl/extract_bds.py`
- Sample: `data/raw/bds/sample/bds2023_msa_sec_sample_2010_2023.csv`

The sample is derived from the official Census BDS `bds2023_msa_sec.csv` bulk file and preserves real field names and source-native `year`, `msa`, and `sector` codes. The full BDS file is not committed. A4.5 records one BDS manifest row and loads raw rows into `raw_bds` with the original source row serialized in `raw_payload`.

A4.5 does not populate `stg_bds`, `int_entrepreneurship`, or `analytics_msa_industry_year`, and it does not map BDS records to July 2023 CBSA or 2022 NAICS standards.

## A4.6 BDS Standardization And Lags

Assignment 4.6 adds the BDS MSA by Sector by Firm Age Coarse sample and moves BDS through `raw_bds` / `raw_bds_firm_age` to `stg_bds` and `int_entrepreneurship`.

Implemented artifacts:

- Raw firm-age sample: `data/raw/bds/sample/bds2023_msa_sec_fac_sample_2010_2023.csv`
- Transform module: `src/regional_entrepreneurship_intelligence/etl/transform_bds.py`
- Transformation documentation: `docs/BDS_TRANSFORMATION.md`

The primary startup concept is firm age 0. A4.6 computes `startup_rate` as age-0 firms divided by all firms in the same source-native MSA-sector-year, multiplied by 100, only when numerator and denominator are usable. `startup_rate_lag1`, `startup_rate_lag2`, and `startup_rate_lag3` are created only in `int_entrepreneurship` after standardization, with calendar-year continuity checks. A4.6 does not ingest QCEW, ACS, or CBP, and it does not create the final integrated analytics table or entrepreneurial-gap target.

## A4.7 QCEW Raw Ingestion

Assignment 4.7 profiles official BLS QCEW annual CSV open data and loads a small official area-slice sample into `raw_qcew`.

Implemented artifacts:

- Source profile: `docs/QCEW_SOURCE_PROFILE.md`
- Loader: `src/regional_entrepreneurship_intelligence/etl/extract_qcew.py`
- Sample: `data/raw/qcew/sample/qcew_annual_area_sample_2022_2023.csv`

The preferred full-scale acquisition path is the official annual by-area bulk file pattern `https://data.bls.gov/cew/data/files/{year}/csv/{year}_annual_by_area.zip`. The committed sample uses official annual area CSV slices for selected Texas counties and preserves the source-native grain:

```text
area_fips x own_code x industry_code x size_code x year x qtr
```

A4.7 records one QCEW manifest row and loads 36 raw rows, including disclosure/status rows, into `raw_qcew`. The loader preserves `area_fips`, `own_code`, `industry_code`, `size_code`, annual measures, disclosure/status columns, and the full row JSON payload.

A4.7 recommends county-level QCEW aggregation to the fixed July 2023 CBSA standard for A4.8, with private-sector ownership (`own_code = 5`) as the default analytical scope. It does not populate `stg_qcew` or `int_industry_growth`, does not calculate growth rates or lags, and does not ingest ACS or CBP.

## A4.8 QCEW Standardization, Growth, And Lags

Assignment 4.8 moves QCEW through `raw_qcew` to `stg_qcew` and `int_industry_growth`.

Implemented artifacts:

- Transform module: `src/regional_entrepreneurship_intelligence/etl/transform_qcew.py`
- Transformation documentation: `docs/QCEW_TRANSFORMATION.md`
- Focused tests: `tests/test_qcew_mapping.py`, `tests/test_qcew_transform.py`, `tests/test_qcew_growth.py`, and `tests/test_qcew_lags.py`

A4.8 uses county-level source rows, maps counties to the fixed July 2023 CBSA reference, and aggregates private-sector (`own_code = 5`) sector-level rows only. Additive measures are summed; average annual pay is recalculated after aggregation. Dollar measures remain nominal.

Growth rates use `(value_t - value_t_minus_1) / value_t_minus_1` with calendar-year continuity checks. Employment and establishment growth receive 1-, 2-, and 3-year lags; payroll and average-pay growth receive one-year lags. A4.8 does not ingest ACS or CBP, join BDS and QCEW, build `analytics_msa_industry_year`, or create entrepreneurial-gap targets.

## A4.9 ACS Raw Ingestion, Regional Controls, And Lags

Assignment 4.9 moves ACS through `raw_acs` to `stg_acs` and `int_regional_controls`.

Implemented artifacts:

- Source profile: `docs/ACS_SOURCE_PROFILE.md`
- Transformation documentation: `docs/ACS_TRANSFORMATION.md`
- Raw loader: `src/regional_entrepreneurship_intelligence/etl/extract_acs.py`
- Transform module: `src/regional_entrepreneurship_intelligence/etl/transform_acs.py`
- Sample: `data/raw/acs/sample/acs5_profile_msa_sample_2020_2023.csv`
- Focused tests: `tests/test_acs_raw_ingestion.py`, `tests/test_acs_mapping.py`, `tests/test_acs_transform.py`, and `tests/test_acs_lags.py`

A4.9 uses ACS 5-year Data Profile API estimates for population, median household income, bachelor degree or higher, labor-force participation, and unemployment. Raw rows preserve estimate and MOE variables. Staging pivots the source-variable rows to MSA-year controls, and the intermediate layer adds population growth and selected one-year lags.

A4.9 does not ingest CBP, merge ACS with BDS/QCEW, build `analytics_msa_industry_year`, or create entrepreneurial-gap targets.

## A4.10 CBP Raw Ingestion And Business Structure

Assignment 4.10 moves CBP through `raw_cbp`, `stg_cbp`, and `int_business_structure`.

Implemented artifacts:

- Source profile: `docs/CBP_SOURCE_PROFILE.md`
- Transformation documentation: `docs/CBP_TRANSFORMATION.md`
- Raw loader: `src/regional_entrepreneurship_intelligence/etl/extract_cbp.py`
- Transform module: `src/regional_entrepreneurship_intelligence/etl/transform_cbp.py`
- Sample: `data/raw/cbp/sample/cbp_county_sector_sample_2022_2023.csv`
- Focused tests: `tests/test_cbp_raw_ingestion.py`, `tests/test_cbp_mapping.py`, and `tests/test_cbp_transform.py`

A4.10 uses official Census CBP API rows at county x NAICS2017 sector x year x legal-form x employment-size grain. County rows are mapped through the July 2023 CBSA county crosswalk, source sectors are checked against the 2022 NAICS sector reference, and additive business-structure measures are summed only for complete, unsuppressed CBSA-sector-year groups.

A4.10 does not merge CBP with BDS, QCEW, or ACS, build `analytics_msa_industry_year`, or create entrepreneurial-gap targets.

## A4.11 Production Instance

The ignored `database/assignment4_production.sqlite` is a separate production
instance of the same schema. National raw, staging, and source-specific
intermediate tables are populated for BDS, QCEW, ACS, and CBP for 2010-2023.
Production counts, historical-definition decisions, and readiness limitations
are documented in `reports/assignment4_production_quality_report.md`. The
committed sample files and tests remain independent. A4.11 does not populate
`analytics_msa_industry_year` or create expected entrepreneurship, alignment,
or entrepreneurial-gap targets.
