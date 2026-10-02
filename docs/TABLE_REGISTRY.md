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
| `raw_bds` | Raw | One source-native BDS row | `raw_bds_id` | `manifest_id`, `pipeline_run_id` | BDS | Yes | Generated in SQLite; sample-loaded in A4.5 | Preserves source-native BDS MSA, sector, year, status values, and raw payload without standardizing geography or NAICS. |
| `raw_qcew` | Raw | One source-native QCEW row | `raw_qcew_id` | `manifest_id`, `pipeline_run_id` | QCEW | Yes | Generated in SQLite | Preserves source-native QCEW identifiers and raw payload. Provisional fields must be verified during ingestion. |
| `raw_cbp` | Raw | One source-native CBP row | `raw_cbp_id` | `manifest_id`, `pipeline_run_id` | CBP | Yes | Generated in SQLite | Preserves source-native CBP identifiers and raw payload. Provisional fields must be verified during ingestion. |
| `raw_acs` | Raw | One source-native ACS row | `raw_acs_id` | `manifest_id`, `pipeline_run_id` | ACS | Yes | Generated in SQLite | Preserves source-native ACS identifiers and raw payload. Provisional fields must be verified during ingestion. |
| `stg_bds` | Staging | MSA x 2-digit NAICS x year where supported by BDS | `stg_bds_id` | `raw_bds_id`, `manifest_id`, `pipeline_run_id`, `geography_id`, `industry_id`, `year` | BDS | Yes | Generated in SQLite | Standardizes BDS entrepreneurship fields while retaining lineage and missing/suppression flags. |
| `stg_qcew` | Staging | MSA x 2-digit NAICS x year where supported by QCEW | `stg_qcew_id` | `raw_qcew_id`, `manifest_id`, `pipeline_run_id`, `geography_id`, `industry_id`, `year` | QCEW | Yes | Generated in SQLite | Standardizes QCEW employment, establishments, payroll, and average pay fields. |
| `stg_cbp` | Staging | MSA x 2-digit NAICS x year where supported by CBP | `stg_cbp_id` | `raw_cbp_id`, `manifest_id`, `pipeline_run_id`, `geography_id`, `industry_id`, `year` | CBP | Yes | Generated in SQLite | Standardizes CBP business-structure fields for validation/context. |
| `stg_acs` | Staging | MSA x year | `stg_acs_id` | `raw_acs_id`, `manifest_id`, `pipeline_run_id`, `geography_id`, `year` | ACS | Yes | Generated in SQLite | Standardizes ACS regional control fields for MSA-year joins. |
| `int_entrepreneurship` | Intermediate | MSA x 2-digit NAICS x year | `(geography_id, industry_id, year)` | `geography_id`, `industry_id`, `year`, `source_manifest_id`, `pipeline_run_id` | BDS-derived | Yes | Generated in SQLite | Holds derived entrepreneurship measures without final gap targets. |
| `int_industry_growth` | Intermediate | MSA x 2-digit NAICS x year | `(geography_id, industry_id, year)` | `geography_id`, `industry_id`, `year`, `source_manifest_id`, `pipeline_run_id` | QCEW-derived | Yes | Generated in SQLite | Holds industry level and growth measures, with nominal/real-adjustment flag. |
| `int_regional_controls` | Intermediate | MSA x year | `(geography_id, year)` | `geography_id`, `year`, `source_manifest_id`, `pipeline_run_id` | ACS-derived | Yes | Generated in SQLite | Holds regional population, income, education, labor-force, and unemployment controls. |
| `int_business_structure` | Intermediate | MSA x 2-digit NAICS x year | `(geography_id, industry_id, year)` | `geography_id`, `industry_id`, `year`, `source_manifest_id`, `pipeline_run_id` | CBP-derived | Yes | Generated in SQLite | Holds business-structure measures used for validation/context. |
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
