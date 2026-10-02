# Assignment 4 Checklist

This checklist maps the Assignment 4 rubric to planned repository evidence. It is intentionally conservative: future work is not marked complete until the artifact actually exists.

## Database Design - 30 pts

| Requirement | Planned evidence | Status |
| --- | --- | --- |
| 3NF design | Normalized schema documentation and implemented database schema | Planned |
| Primary keys and foreign keys | Schema SQL or database utility code defining PK/FK relationships | Planned |
| Constraints | Schema implementation with type, nullability, uniqueness, and check constraints where appropriate | Planned |
| Indexing | Documented indexes for lookup, joins, and analytical query paths | Planned |
| ERD | Formal ERD in `docs/` | Planned |
| Schema matching implementation | Database creation code aligned with ERD and data dictionary | Planned |
| A4.1 architecture conventions | `docs/DATA_ARCHITECTURE.md` | Complete |

## ETL Implementation - 30 pts

| Requirement | Planned evidence | Status |
| --- | --- | --- |
| BDS extract | Source-specific extraction module under `src/regional_entrepreneurship_intelligence/etl/` | Planned |
| QCEW extract | Source-specific extraction module under `src/regional_entrepreneurship_intelligence/etl/` | Planned |
| CBP extract | Source-specific extraction module under `src/regional_entrepreneurship_intelligence/etl/` | Planned |
| ACS extract | Source-specific extraction module under `src/regional_entrepreneurship_intelligence/etl/` | Planned |
| Transformations | Staging and intermediate transformation modules | Planned |
| Loading | Database loading utilities under `src/regional_entrepreneurship_intelligence/database/` | Planned |
| Logging | Pipeline logging to `logs/` with generated logs normally ignored by Git | Planned |
| Error handling | Explicit exceptions, bad-record handling, and rejected-record outputs | Planned |
| Rerunnability | Documented idempotency or rerun evidence | Planned |
| Target pipeline command documented | `uv run python -m regional_entrepreneurship_intelligence.etl.run_pipeline` | Complete |

## Data Quality - 20 pts

| Requirement | Planned evidence | Status |
| --- | --- | --- |
| Validation framework | Reusable validation logic under `src/regional_entrepreneurship_intelligence/validation/` | Planned |
| Row counts | Quality report with source, staging, intermediate, and analytics row counts | Planned |
| Missingness | Quality report with missingness by source and key variable | Planned |
| Duplicates | Duplicate-key checks at relevant grains | Planned |
| Rejected records | Rejected-record table or file with reason codes | Planned |
| Actions on bad records | Documentation explaining whether records are rejected, retained with flags, or reviewed | Planned |
| Quality report | Generated report under `reports/` or documented output path | Planned |
| Bad-record policy documented | `docs/DATA_ARCHITECTURE.md` | Complete |
| Suppression policy documented | `docs/DATA_ARCHITECTURE.md` | Complete |

## Documentation & Code Quality - 20 pts

| Requirement | Planned evidence | Status |
| --- | --- | --- |
| ERD | Formal diagram in `docs/` | Planned |
| Data dictionary | Field-level dictionary for tables and analytical variables | Planned |
| ETL documentation | Source-specific and end-to-end pipeline documentation | Planned |
| Docstrings | Docstrings in ETL, database, and validation modules | Planned |
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
