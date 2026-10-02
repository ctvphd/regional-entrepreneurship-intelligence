# Assignment 4 Data Architecture

## Purpose

This document records the Assignment 4.1 repository audit and data architecture setup for the Regional Entrepreneurship Intelligence project. It establishes conventions for later database design and ETL implementation without beginning live data extraction, schema creation, ERD design, or production pipeline work.

## Research Grain

The planned clean analytical panel will use:

```text
Metropolitan Statistical Area x 2-digit NAICS industry x year
```

The primary study window is 2010-2023. The architecture should remain extensible to earlier years if later compatibility checks justify adding them.

## Primary Sources

Planned source systems:

- Census Business Dynamics Statistics (BDS)
- BLS Quarterly Census of Employment and Wages (QCEW)
- Census County Business Patterns (CBP)
- American Community Survey (ACS)

Planned acquisition strategy:

- ACS: API
- QCEW: official bulk files
- BDS: API or bulk file depending on final feasibility
- CBP: API initially, bulk files if scale makes that more appropriate

No source should flow directly from an API or download into the final clean analytical table. Every source must first pass through the raw layer.

## Layered Architecture

```text
Official Data Sources
        |
        v
   Reference Layer
        |
        v
     Raw Layer
        |
        v
    Staging Layer
        |
        v
 Intermediate Layer
        |
        v
   Analytics Layer
        |
        v
 Model-Ready Layer
```

### Reference Layer

Reference and crosswalk structures support geography, industry, source, and year alignment. Examples include geography mappings, NAICS mappings, CPI or deflator reference data, and source lookup tables.

### Raw Layer

The raw layer stores source-faithful extracts. Raw data should preserve original values, source-native identifiers, source-native geography, source-native NAICS values, and suppression indicators. Raw source downloads should generally not be committed to Git.

### Staging Layer

The staging layer standardizes types, names, formats, and basic source-specific parsing while preserving traceability to raw records. Staging should not silently discard bad records.

### Intermediate Layer

The intermediate layer contains domain-specific transformations such as entrepreneurship measures, industry growth measures, regional controls, and business-structure summaries.

### Analytics Layer

The analytics layer contains analysis-ready tables. The planned primary clean table name is:

```text
analytics_msa_industry_year
```

### Model-Ready Layer

The model-ready layer may exist structurally for later assignments, but Assignment 4.1 does not create final machine-learning targets or fold-specific derived outcomes.

## Directory Purposes

| Path | Purpose |
| --- | --- |
| `data/raw/` | Source-faithful extracts. No substantive transformations. Preserve original values, suppression, and source-native identifiers. Large files are not committed. |
| `data/interim/` | Intermediate file artifacts produced during cleaning and transformation. Not authoritative source data and not final analytical data. |
| `data/processed/` | Final permitted file-based outputs such as clean analytical samples or export files. The canonical structured analytical store will ultimately be the database. |
| `data/external/reference/` | Reference and crosswalk files such as geography mappings, NAICS mappings, CPI/deflator files, and small lookup files. |
| `database/` | SQLite database location. Planned database name: `regional_entrepreneurship.sqlite`. The full database is not built in A4.1. |
| `logs/` | Pipeline execution logs. Generated logs are normally ignored unless a small example is intentionally committed. |
| `reports/` | Generated quality reports or permitted run summaries. |
| `src/regional_entrepreneurship_intelligence/etl/` | Importable extract, transform, and load modules. |
| `src/regional_entrepreneurship_intelligence/database/` | Schema creation, connection management, loading, and related database utilities. |
| `src/regional_entrepreneurship_intelligence/validation/` | Reusable validation and quality-check logic. |
| `tests/` | Automated tests. |
| `docs/` | Human-readable project documentation. |

## Geography Strategy

Raw data should preserve source-native geography. The analytical layer will later use standardized CBSA/MSA identifiers. This step does not hard-code changing historical MSA definitions. Geography-vintage decisions should be implemented later through reference and crosswalk structures.

## Industry Strategy

Raw data should preserve native NAICS values and any available NAICS vintage or version metadata. The analytical layer will later standardize to 2-digit NAICS.

## Table Naming Conventions

| Layer | Prefix | Examples |
| --- | --- | --- |
| Reference | `ref_` | `ref_geography`, `ref_industry`, `ref_year`, `ref_source` |
| Raw | `raw_` | `raw_bds`, `raw_qcew`, `raw_cbp`, `raw_acs` |
| Staging | `stg_` | `stg_bds`, `stg_qcew`, `stg_cbp`, `stg_acs` |
| Intermediate | `int_` | `int_entrepreneurship`, `int_industry_growth`, `int_regional_controls`, `int_business_structure` |
| Analytics | `analytics_` | `analytics_msa_industry_year` |
| Metadata / quality | `metadata_`, `quality_` | `metadata_source_manifest`, `metadata_pipeline_run`, `quality_rejected_record`, `quality_table_metric` |

The Assignment 4.2 schema implements these conventions in `src/regional_entrepreneurship_intelligence/database/schema.py`.

## File Naming Conventions

Project-created files should generally use:

- lowercase
- snake_case
- source name
- year when relevant
- no spaces

Examples:

- `qcew_2019.csv`
- `bds_msa_sector_2020.csv`
- `acs_cbsa_2022.csv`

External raw files do not need to be renamed merely for cosmetic reasons when retaining the official source filename provides better provenance.

## Raw-Data Policy And Safe Review Path

Large, confidential, restricted, licensed, or oversized raw data must not be committed. Public source data may still be too large to commit.

Repository policy:

- Raw source downloads should generally be Git-ignored.
- Permitted small samples may be committed when useful.
- Synthetic samples may be used when needed.
- Scripts and metadata must make the true sources reproducible.
- Another authorized user must be able to determine how to acquire the real source data.
- Raw, missing, and suppressed values must remain distinguishable.

## Source Manifest Design

Every future source ingestion should capture metadata with at least:

- `source_name`
- `source_agency`
- `dataset_name`
- `access_method`
- `source_url_or_endpoint`
- `retrieval_timestamp`
- `source_year`
- `source_version`
- `raw_filename`
- `file_checksum`
- `row_count`
- `notes`

These fields describe the intended manifest design only. A4.1 does not fabricate source-manifest values.

## Pipeline Run Metadata

Future pipeline runs should eventually record:

- `pipeline_run_id`
- `start_timestamp`
- `end_timestamp`
- `status`
- `stage`
- `records_read`
- `records_written`
- `records_rejected`
- `warnings`
- `error_message`

No external workflow orchestration service is required for the planned Assignment 4 implementation.

## Rejected-Record Policy

Records should never be silently discarded. Potential reason codes include:

- `invalid_cbsa`
- `invalid_naics`
- `invalid_year`
- `duplicate_key`
- `missing_required_field`
- `invalid_numeric_value`
- `suppressed_value`
- `failed_reference_match`

Not every suppressed observation should be rejected. Suppression treatment will depend on the analytical requirement. The architectural rule is that bad, missing, and suppressed records must be explicitly handled and documented.

## Suppression And Missingness Policy

Suppressed observations must never be converted to zero. Missing and suppressed observations must remain distinguishable from each other and from true numeric zero values.

## Lineage Principle

Every analytical value should eventually be traceable backward through:

```text
analytics -> intermediate -> staging -> raw -> source
```

## Modeling-Leakage Constraint

The project must not globally calculate:

- expected entrepreneurship
- entrepreneurial alignment residual
- final entrepreneurial-gap target

Those values should later be calculated within temporal training folds when appropriate. A4.1 does not create model targets.

## Intended End-To-End Command

The planned final pipeline interface is:

```powershell
uv run python -m regional_entrepreneurship_intelligence.etl.run_pipeline
```

The command will eventually:

1. extract
2. ingest raw data
3. transform
4. validate
5. load
6. generate quality metrics
7. log execution

A4.1 only established this as the target interface. Assignment 4.2 adds a separate schema initialization command:

```powershell
uv run python -m regional_entrepreneurship_intelligence.database.schema
```

This command initializes the SQLite schema at `database/regional_entrepreneurship.sqlite`. It does not download source data or run the final ETL pipeline.

## Implemented Assignment 4.2 Schema

Assignment 4.2 implements the normalized SQLite schema, table registry, ERD, and data dictionary.

Implemented schema artifacts:

- `src/regional_entrepreneurship_intelligence/database/connection.py`
- `src/regional_entrepreneurship_intelligence/database/schema.py`
- `docs/TABLE_REGISTRY.md`
- `docs/ERD.md`
- `docs/data_dictionary.md`
- `tests/test_schema.py`

The physical SQLite database file remains ignored by Git. The schema code is safe to rerun and uses `CREATE TABLE IF NOT EXISTS`.

## Indexing Strategy

Assignment 4.2 implements indexes for:

- CBSA and NAICS reference lookup
- source manifest lookup by source/year
- pipeline run status/stage lookup
- source-native raw key review
- staging grain access
- intermediate and analytics year filtering
- quality/rejected-record review

Indexes are intentionally moderate until real query patterns emerge during later Assignment 4 work.

## Implemented Assignment 4.3 Reference And Metadata Framework

Assignment 4.3 adds reference seed helpers, metadata helpers, tests, and documentation without starting live source ingestion.

Implemented artifacts:

- `src/regional_entrepreneurship_intelligence/database/reference.py`
- `src/regional_entrepreneurship_intelligence/database/metadata.py`
- `tests/test_reference_data.py`
- `tests/test_metadata.py`

The reference helper populates:

- `ref_year`: exactly the 14 primary study years, 2010-2023
- `ref_source`: Census Business Dynamics Statistics (BDS), BLS Quarterly Census of Employment and Wages (QCEW), Census County Business Patterns (CBP), and American Community Survey (ACS)

The helper does not populate `ref_geography` or `ref_industry`. Those tables require authoritative CBSA/geography and NAICS references or crosswalks. Fabricating rows would create false lineage and could corrupt later joins, so they remain structural until verified source files are available.

The metadata helper supports inserting source-manifest rows, starting/updating/finishing pipeline-run rows, storing quality metrics, and recording rejected records. The tests use temporary SQLite databases and synthetic metadata records only; they do not pollute the project database, download source data, or call external APIs.

## Implemented Assignment 4.4 Geography And NAICS References

Assignment 4.4 loads small authoritative public reference files from official Census sources into the reference layer. These assets are stored in `data/external/reference/` with official filenames preserved.

Implemented A4.4 artifacts:

- `data/external/reference/list1_2023.xlsx`
- `data/external/reference/2022_NAICS_Structure.xlsx`
- `data/external/reference/2022_to_2017_NAICS.xlsx`
- `data/external/reference/2017_to_2022_NAICS.xlsx`
- `data/external/reference/2017_to_2012_NAICS.xlsx`
- `data/external/reference/2012_to_2017_NAICS.xlsx`
- `tests/test_geography_reference.py`
- `tests/test_industry_reference.py`

The loader command is:

```powershell
uv run python -m regional_entrepreneurship_intelligence.database.reference
```

The command initializes the schema if needed, records reference-file manifests, and loads geography and industry reference tables. It does not ingest BDS, QCEW, CBP, or ACS data.

### Geography Standardization

The selected geography standard is the U.S. Census Bureau July 2023 CBSA delineation List 1 file. The file reflects OMB/Census metropolitan and micropolitan delineations based on the 2020 standards. A4.4 uses this as a fixed-vintage reference framework for later mapping of source records.

Loaded geography tables:

- `ref_geography`: one row per CBSA/source vintage
- `ref_geography_county_crosswalk`: one row per CBSA/county/source vintage

The July 2023 vintage is preserved in `source_vintage`. `valid_from_year` and `valid_to_year` remain null because the selected workbook identifies a delineation vintage but does not provide record-level historical validity periods. Later ingestion should map source-native county or CBSA identifiers to this fixed reference vintage instead of silently mixing CBSA vintages.

The county crosswalk table is needed because county-to-CBSA membership is a different grain from the CBSA area table. It will support later QCEW/CBP county aggregation and geography validation.

### NAICS Standardization

The analytical industry reference standard is the U.S. Census Bureau 2022 NAICS Structure with Change Indicator. A4.4 loads the 2022 hierarchy into `ref_industry`, including official combined two-digit sectors such as `31-33`, `44-45`, and `48-49`.

The study period spans 2010-2023, so relevant NAICS versions include 2012, 2017, and 2022. Official Census concordance files for 2012-to-2017, 2017-to-2012, 2017-to-2022, and 2022-to-2017 are preserved as reference assets and recorded in the source manifest. A4.4 does not apply speculative mappings across versions; source-specific transformation should decide how to use concordances once each source's native NAICS vintage is verified.

## Implemented Assignment 4.5 BDS Source Profiling And Raw Ingestion

Assignment 4.5 profiles the official Census BDS source family and loads a permitted source-native BDS sample into the raw database layer.

Implemented A4.5 artifacts:

- `docs/BDS_SOURCE_PROFILE.md`
- `src/regional_entrepreneurship_intelligence/etl/extract_bds.py`
- `data/raw/bds/sample/bds2023_msa_sec_sample_2010_2023.csv`
- `tests/test_bds_raw_ingestion.py`

The selected source family is the official Census BDS 2023 release. A4.5 uses the bulk CSV approach rather than the API because the API requires a key and the official bulk files are directly reproducible. The profiled file is `bds2023_msa_sec.csv`, which supports the source-native grain:

```text
year x msa x sector
```

The committed sample covers 2010-2023 for selected MSAs and sectors. It is not the full dataset and must not be treated as complete analytical input.

Raw ingestion stores:

- `source_year` from BDS `year`
- `source_geography_id` from BDS `msa`
- `source_industry_id` from BDS `sector`
- source-native row identifiers
- the complete BDS row in `raw_payload`
- suppression/status preservation for `D`, `N`, `S`, and `X` values

A4.5 explicitly does not standardize BDS geography to the July 2023 CBSA reference, standardize BDS industry to 2022 NAICS, calculate startup rates, create lag variables, or populate `stg_bds` or `int_entrepreneurship`.

## Implemented Assignment 4.6 BDS Standardization And Lag Framework

Assignment 4.6 adds a dedicated BDS firm-age raw sample, mapping audits, BDS staging, intermediate entrepreneurship construction, and startup-rate lags.

Implemented A4.6 artifacts:

- `data/raw/bds/sample/bds2023_msa_sec_fac_sample_2010_2023.csv`
- `src/regional_entrepreneurship_intelligence/etl/transform_bds.py`
- `docs/BDS_TRANSFORMATION.md`
- `tests/test_bds_mapping.py`
- `tests/test_bds_transform.py`
- `tests/test_bds_lags.py`

BDS native industry is treated as 2017 NAICS sector coding. The analytical reference remains 2022 NAICS. A4.6 validates comparability at the sector level and preserves combined sectors such as `31-33` and `44-45`; it does not apply blanket NAICS conversion.

The primary startup measure uses BDS firm-age-coarse age-0 rows. The implemented rate is:

```text
startup_rate = age_0_firms / all_firms * 100
```

The denominator comes from the BDS MSA-sector backbone for the same source-native MSA-sector-year. Suppressed, unavailable, nonnumeric, or zero-denominator cases remain null and are not converted to zero.

Startup-rate lags are created only in `int_entrepreneurship`, after geography and industry standardization. Lags use calendar-year continuity within `geography_id x industry_id` panels and do not forward-fill across missing years, MSAs, sectors, or suppressed prior values.

## Implemented Assignment 4.7 QCEW Source Profiling And Raw Ingestion

Assignment 4.7 profiles official BLS QCEW annual CSV open data and loads a small official source-native sample into the raw database layer.

Implemented A4.7 artifacts:

- `docs/QCEW_SOURCE_PROFILE.md`
- `src/regional_entrepreneurship_intelligence/etl/extract_qcew.py`
- `data/raw/qcew/sample/qcew_annual_area_sample_2022_2023.csv`
- `tests/test_qcew_raw_ingestion.py`

The preferred full-scale QCEW acquisition path is the official annual by-area bulk file pattern:

```text
https://data.bls.gov/cew/data/files/{year}/csv/{year}_annual_by_area.zip
```

The A4.7 sample uses official annual area CSV slices for selected Texas counties and years 2022-2023. It preserves the source-native QCEW grain:

```text
area_fips x own_code x industry_code x size_code x year x qtr
```

Raw ingestion stores:

- `source_year` from QCEW `year`
- `source_geography_id` from QCEW `area_fips`
- `source_industry_id` from QCEW `industry_code`
- `source_ownership_code` from QCEW `own_code`
- `source_size_code` from QCEW `size_code`
- annual establishments, employment, wages, and pay as source text
- QCEW disclosure/status values
- the complete QCEW row in `raw_payload`

The recommended A4.8 geography strategy is to aggregate county-level QCEW rows to the fixed July 2023 CBSA reference using `ref_geography_county_crosswalk`, rather than assuming historical QCEW MSA area codes directly match the analytical geography vintage. The recommended analytical ownership scope is private sector, `own_code = 5`, unless a later research decision documents another scope.

A4.7 explicitly does not populate `stg_qcew` or `int_industry_growth`, calculate QCEW growth rates or lags, ingest ACS or CBP, or create the final integrated analytics table.

## Implemented Assignment 4.8 QCEW Standardization And Lag Framework

Assignment 4.8 standardizes QCEW county-level annual rows to the fixed July 2023 CBSA geography and constructs nominal industry-growth measures.

Implemented A4.8 artifacts:

- `src/regional_entrepreneurship_intelligence/etl/transform_qcew.py`
- `docs/QCEW_TRANSFORMATION.md`
- `tests/test_qcew_mapping.py`
- `tests/test_qcew_transform.py`
- `tests/test_qcew_growth.py`
- `tests/test_qcew_lags.py`

A4.8 selects county aggregation over direct historical MSA records because county identifiers provide the clearest path to the fixed July 2023 CBSA reference. The selected ownership scope is private ownership, `own_code = 5`, to avoid double counting total and ownership-specific records.

The QCEW intermediate grain is:

```text
geography_id x industry_id x year
```

Conceptually this is `MSA/CBSA x 2022 NAICS 2-digit sector x year`. Additive measures are summed across counties, and average annual pay is recalculated after aggregation. Dollar measures remain nominal. Growth rates and lags require calendar-year continuity within each geography-industry panel.

A4.8 does not ingest ACS or CBP, join BDS and QCEW, build the final analytics table, or create model targets.

## Implemented Assignment 4.9 ACS Regional Controls

Assignment 4.9 ingests a small official ACS 5-year Data Profile API sample and builds MSA-year regional controls.

Implemented A4.9 artifacts:

- `data/raw/acs/sample/acs5_profile_msa_sample_2020_2023.csv`
- `src/regional_entrepreneurship_intelligence/etl/extract_acs.py`
- `src/regional_entrepreneurship_intelligence/etl/transform_acs.py`
- `docs/ACS_SOURCE_PROFILE.md`
- `docs/ACS_TRANSFORMATION.md`
- `tests/test_acs_raw_ingestion.py`
- `tests/test_acs_mapping.py`
- `tests/test_acs_transform.py`
- `tests/test_acs_lags.py`

ACS is regional data, not industry-level data. The A4.9 intermediate grain is:

```text
geography_id x year
```

Conceptually this is `MSA/CBSA x year`. The controls are total population, median household income, bachelor degree or higher percentage, labor-force participation percentage, and unemployment rate. ACS MOEs are preserved in raw and staging, while the intermediate layer uses point estimates.

A4.9 does not ingest CBP, merge ACS with BDS/QCEW, build the final analytics table, duplicate ACS by industry, or create model targets.
