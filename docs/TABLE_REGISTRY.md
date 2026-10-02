# Table Registry

This registry defines the Assignment 4 SQLite schema. It documents the planned table grain, layer, keys, business rule, and current population status for every implemented table. Raw tables are intentionally flexible and source-faithful; standardized reference, staging, intermediate, analytics, metadata, and quality tables are normalized where practical.

Assignment 4.3 populates only verified deterministic reference records: `ref_year` contains the 14 primary study years from 2010 through 2023, and `ref_source` contains the four approved source systems. `ref_geography` and `ref_industry` remain structural only until authoritative CBSA/geography and NAICS reference files or crosswalks are added. No geography or industry rows are fabricated.

| Table | Layer | Grain | PK | Main FKs | Source | Materialized? | Committed or generated | Purpose |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ref_geography` | Reference | One standardized geography record per CBSA/source vintage | `geography_id` | None | Reference/crosswalk | Yes | Generated in SQLite; structural only in A4.3 | Stores standardized CBSA/MSA geography references without hard-coding historical crosswalk logic. |
| `ref_industry` | Reference | One NAICS record per NAICS code/version | `industry_id` | None | Reference/crosswalk | Yes | Generated in SQLite; structural only in A4.3 | Stores standardized NAICS references with version metadata. |
| `ref_year` | Reference | One row per calendar year | `year` | None | Deterministic reference | Yes | Generated and seeded in SQLite | Identifies the 2010-2023 primary study years; A4.3 seeds exactly 14 rows. |
| `ref_source` | Reference | One row per source registry entry | `source_id` | None | Project metadata | Yes | Generated and seeded in SQLite | Registers the four approved planned source datasets and agencies. |
| `metadata_source_manifest` | Metadata | One row per retrieved source file or API result | `manifest_id` | `source_id` -> `ref_source` | Pipeline metadata | Yes | Generated in SQLite | Records provenance, access method, source version, raw filename, checksum, and row count. |
| `metadata_pipeline_run` | Metadata | One row per pipeline stage run | `pipeline_run_id` | None | Pipeline metadata | Yes | Generated in SQLite | Records run status, timing, stage, counts, warnings, and errors. |
| `raw_bds` | Raw | One source-native BDS row | `raw_bds_id` | `manifest_id`, `pipeline_run_id` | BDS | Yes | Generated in SQLite | Preserves source-native BDS identifiers and raw payload. Provisional fields must be verified during ingestion. |
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
