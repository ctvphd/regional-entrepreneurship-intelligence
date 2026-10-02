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
| Metadata / quality | `metadata_`, `quality_`, `rejected_` | `metadata_source_manifest`, `quality_pipeline_run`, `rejected_staging_records` |

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
