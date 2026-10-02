# Assignment 4 Checklist

This checklist maps the Assignment 4 rubric to planned repository evidence. It is intentionally conservative: future work is not marked complete until the artifact actually exists.

## Database Design - 30 pts

| Requirement | Planned evidence | Status |
| --- | --- | --- |
| 3NF design | Normalized schema documentation and implemented database schema | Complete |
| Primary keys and foreign keys | Schema SQL or database utility code defining PK/FK relationships | Complete |
| Constraints | Schema implementation with type, nullability, uniqueness, and check constraints where appropriate | Complete |
| Indexing | Documented indexes for lookup, joins, and analytical query paths | Complete |
| ERD | Formal ERD in `docs/` | Complete |
| Schema matching implementation | Database creation code aligned with ERD and data dictionary | Complete |
| A4.1 architecture conventions | `docs/DATA_ARCHITECTURE.md` | Complete |
| Reference year/source seed data | Deterministic `ref_year` and approved `ref_source` helpers with tests | Complete |
| Authoritative geography/industry references | Census CBSA and NAICS assets, loader, schema updates, and tests | Complete |
| BDS firm-age raw structure | Dedicated BDS firm-age raw table and schema tests | Complete |

## ETL Implementation - 30 pts

| Requirement | Planned evidence | Status |
| --- | --- | --- |
| BDS extract | Source-specific extraction module under `src/regional_entrepreneurship_intelligence/etl/` | Complete |
| QCEW extract | Source-specific extraction module under `src/regional_entrepreneurship_intelligence/etl/` | Complete |
| CBP extract | Source-specific extraction module under `src/regional_entrepreneurship_intelligence/etl/` | Complete |
| ACS extract | Source-specific extraction module under `src/regional_entrepreneurship_intelligence/etl/` | Complete |
| BDS transformations | BDS staging, entrepreneurship intermediate, mapping audits, and lag construction | Complete |
| Other source transformations | QCEW, ACS, and CBP transformations complete through source-specific intermediate layers | Complete |
| Loading | Database loading utilities under `src/regional_entrepreneurship_intelligence/database/` | Complete |
| Logging | Pipeline logging to `logs/` with generated logs normally ignored by Git | Planned |
| Error handling | Explicit exceptions, bad-record handling, and rejected-record outputs | Complete |
| Rerunnability | Documented idempotency or rerun evidence | Complete |
| Target pipeline command documented | `uv run python -m regional_entrepreneurship_intelligence.etl.run_pipeline` | Complete |
| Metadata helper utilities | Source manifest, pipeline run, quality metric, and rejected-record helpers | Complete |

## Data Quality - 20 pts

| Requirement | Planned evidence | Status |
| --- | --- | --- |
| Validation framework | Reusable validation logic under `src/regional_entrepreneurship_intelligence/validation/` | Planned |
| Reference row counts | A4.4 loader/test evidence for geography, county crosswalk, industry, and manifests | Complete |
| BDS quality metrics | A4.6 quality metrics for BDS raw, staging, intermediate, mapping, missingness, and lag checks | Complete |
| QCEW raw quality checks | A4.7 QCEW raw row-count, manifest, status-row, and duplicate-key tests | Complete |
| QCEW transformation quality checks | A4.8 QCEW mapping, aggregation, growth, lag, duplicate-key, and idempotency tests | Complete |
| ACS quality checks | A4.9 ACS raw-ingestion, geography, MSA-year transform, population-growth, lag, duplicate-key, and idempotency tests | Complete |
| CBP quality checks | A4.10 CBP raw-ingestion, geography/industry mapping, complete county coverage, duplicate-key, rejected-record, and idempotency tests | Complete |
| Row counts | Quality report with source, staging, intermediate, and analytics row counts | Planned |
| Missingness | Quality report with missingness by source and key variable | Planned |
| Duplicates | Duplicate-key checks at relevant grains | Complete |
| Rejected records | Rejected-record table or file with reason codes | Complete |
| Actions on bad records | Documentation explaining whether records are rejected, retained with flags, or reviewed | Complete |
| Quality report | Generated report under `reports/` or documented output path | Planned |
| Bad-record policy documented | `docs/DATA_ARCHITECTURE.md` | Complete |
| Suppression policy documented | `docs/DATA_ARCHITECTURE.md` | Complete |

## Documentation & Code Quality - 20 pts

| Requirement | Planned evidence | Status |
| --- | --- | --- |
| ERD | Formal diagram in `docs/` | Complete |
| Data dictionary | Field-level dictionary for tables and analytical variables | Complete |
| ETL documentation | Source-specific and end-to-end pipeline documentation | Complete |
| Docstrings | Docstrings in ETL, database, and validation modules | In progress |
| Setup instructions | README and Assignment 4 documentation | Planned |
| Safe review path | Raw-data policy and reproducibility guidance in `docs/DATA_ARCHITECTURE.md` | Complete |
| Git history | Meaningful commits for Assignment 4 segments | In progress |
| AI disclosure | Current entries in `docs/AI_USE.md` | Complete |

## A4.1 Stop Line

A4.1 stops after repository audit and data architecture setup. The following are explicitly deferred:

- schema creation
- ERD design
- reference-table implementation
- database implementation
- BDS ingestion
- QCEW ingestion
- CBP ingestion
- ACS ingestion

## A4.3 Stop Line

A4.3 completes a small reference and metadata framework only. It seeds `ref_year` and `ref_source`, adds helper functions for metadata and quality records, and tests those helpers in temporary SQLite databases. It explicitly does not:

- ingest BDS, QCEW, CBP, or ACS data
- download full source datasets
- fabricate geography, CBSA, NAICS, or industry reference rows
- begin Assignment 4.4 transformations or pipeline execution

## A4.4 Stop Line

A4.4 completes authoritative geography and NAICS reference loading only. It loads Census CBSA and NAICS reference assets, records manifests, validates uniqueness and foreign-key compatibility, and verifies rerun behavior. It explicitly does not:

- ingest BDS, QCEW, CBP, or ACS observations
- calculate startup rates, lag variables, employment growth, or analytical targets
- apply speculative NAICS crosswalk mappings
- mix multiple CBSA vintages inside the reference layer
- begin Assignment 4.5

## A4.5 Stop Line

A4.5 completes BDS source profiling, native-vintage review, and raw sample ingestion only. It profiles official BDS bulk/API options, commits a small permitted source-native BDS sample, loads `raw_bds`, records a manifest, and verifies raw-ingestion idempotency. It explicitly does not:

- create `stg_bds`
- calculate startup rates or lag variables
- map BDS geography to the July 2023 CBSA standard
- map BDS sectors to the 2022 NAICS reference
- populate `int_entrepreneurship`
- ingest QCEW, CBP, or ACS
- begin Assignment 4.6

## A4.6 Stop Line

A4.6 completes BDS standardization, startup construction, and lag framework only. It adds BDS firm-age raw ingestion, geography and industry mapping audits, `stg_bds`, `int_entrepreneurship`, and startup-rate lags. It explicitly does not:

- ingest QCEW, ACS, or CBP
- create industry-growth measures
- build `analytics_msa_industry_year`
- create expected entrepreneurship, alignment residuals, or entrepreneurial-gap targets
- begin Assignment 4.7

## A4.7 Stop Line

A4.7 completes QCEW source profiling and raw sample ingestion only. It profiles official BLS QCEW annual CSV open data, commits a small official annual area-slice sample, loads `raw_qcew`, records a manifest, and verifies raw-ingestion idempotency. It explicitly does not:

- create `stg_qcew`
- populate `int_industry_growth`
- calculate QCEW employment, establishment, payroll, or pay growth
- create QCEW lags
- aggregate QCEW county rows to CBSA
- standardize QCEW industry codes to 2022 NAICS
- ingest ACS or CBP
- build `analytics_msa_industry_year`
- create expected entrepreneurship, alignment residuals, or entrepreneurial-gap targets
- begin Assignment 4.8

## A4.8 Stop Line

A4.8 completes QCEW standardization, industry-growth construction, and growth-lag framework only. It moves QCEW through `raw_qcew`, `stg_qcew`, and `int_industry_growth`; records mapping/exclusion/coverage quality metrics; and documents county aggregation, private ownership, nominal-dollar treatment, growth formulas, and lag formulas. It explicitly does not:

- ingest ACS
- ingest CBP
- join BDS and QCEW
- build `analytics_msa_industry_year`
- create expected entrepreneurship
- create alignment residuals
- create entrepreneurial-gap targets
- begin Assignment 4.9

## A4.9 Stop Line

A4.9 completes ACS raw acquisition, regional-control construction, and one-year regional-control lag framework only. It moves ACS through `raw_acs`, `stg_acs`, and `int_regional_controls`; records geography/missingness/duplicate/lag quality metrics; and documents ACS product choice, variables, MOE preservation, population growth, income treatment, and lag rules. It explicitly does not:

- ingest CBP
- merge ACS with BDS or QCEW
- duplicate ACS controls by industry
- build `analytics_msa_industry_year`
- create expected entrepreneurship
- create alignment residuals
- create entrepreneurial-gap targets
- begin Assignment 4.10

## A4.10 Stop Line

A4.10 completes CBP raw acquisition, county-to-CBSA business-structure construction, and quality checks only. It moves CBP through `raw_cbp`, `stg_cbp`, and `int_business_structure`; records mapping, suppression, incomplete-coverage, duplicate, and rejected-record metrics; and documents CBP source fields, 2017 NAICS source coding, 2022 NAICS analytical checks, and payroll units. It explicitly does not:

- merge CBP with BDS, QCEW, or ACS
- build `analytics_msa_industry_year`
- create expected entrepreneurship
- create alignment residuals
- create entrepreneurial-gap targets
- begin Assignment 4.11
