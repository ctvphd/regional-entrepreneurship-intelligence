# AI Use Disclosure

## Tools Used

- Codex/OpenAI-assisted development

## Current Use

AI assistance was used for:

- repository architecture
- environment configuration guidance
- documentation drafting
- Git workflow assistance

## Student Responsibility

The student remains responsible for:

- understanding the code and repository structure
- validating generated work
- testing outputs
- complying with course policies

## Update Log

| Date | Tool | Task | Verification |
| ---- | ---- | ---- | ------------ |
| 2026-08-30 | Codex/OpenAI-assisted development | Assignment 2 repository setup, environment configuration, documentation, and Git workflow assistance | Student review and local verification commands |
| 2026-08-30 | Codex/OpenAI-assisted development | Updated project geographic framing from a fixed regional pilot to a scalable Metropolitan Statistical Area (MSA), Micropolitan Statistical Area, and County architecture | Git diff review and local Git status verification |
| 2026-09-10 | Codex/OpenAI-assisted development | Public-data feasibility testing, API/data-source integration guidance, diagnostic analysis, and documentation for the proposed regional entrepreneurship model | Feasibility script execution, notebook code-cell verification, source checks, and Git diff review |
| 2026-09-27 | Codex/OpenAI-assisted development | Assignment 3 proposal submission-readiness review, PDF placement, scientific-method checklist review, and Git/GitHub workflow support | PDF text extraction, rendered-page inspection, repository status checks, and Git diff review |
| 2026-09-27 | Codex/OpenAI-assisted development | Created a Markdown companion version of the Assignment 3 proposal from the submitted PDF content | PDF-to-Markdown consistency checks and Git diff review |
| 2026-10-02 | Codex/OpenAI-assisted development | Assignment 4.1 repository audit, data architecture documentation, directory scaffold setup, `.gitignore` review, and Git/GitHub workflow support | Repository structure review, documentation review, Git status checks, and Git diff review |
| 2026-10-02 | Codex/OpenAI-assisted development | Assignment 4.2 SQLite schema organization, normalization review, ERD/table-registry drafting, data-dictionary skeleton generation, and schema smoke-test support | Schema initialization, unittest smoke test, documentation review, and Git diff review |
| 2026-10-02 | Codex/OpenAI-assisted development | Assignment 4.3 reference-table implementation, metadata helper design, unit-test planning, documentation updates, and Git/GitHub workflow support | Temporary SQLite unittest execution, reference row-count checks, documentation review, and Git diff review |
| 2026-10-02 | Codex/OpenAI-assisted development | Assignment 4.4 authoritative source selection, CBSA/NAICS reference loading, validation design, crosswalk planning, documentation updates, and Git/GitHub workflow support | Official Census source checks, checksum/manifest recording, idempotent loader tests, unittest discovery, and Git diff review |
| 2026-10-02 | Codex/OpenAI-assisted development | Assignment 4.5 BDS source profiling, native geography/industry review, raw-ingestion architecture, validation planning, documentation updates, and Git/GitHub workflow support | Official Census BDS source checks, raw sample creation, temporary SQLite ingestion tests, idempotency checks, unittest discovery, and Git diff review |
| 2026-10-02 | Codex/OpenAI-assisted development | Assignment 4.6 BDS geography mapping audit, NAICS comparability audit, startup measure construction, lag design, validation planning, documentation updates, and Git/GitHub workflow support | Temporary SQLite transformation tests, lag panel-gap tests, idempotency checks, quality-metric review, unittest discovery, and Git diff review |
| 2026-10-02 | Codex/OpenAI-assisted development | Assignment 4.7 QCEW source profiling, annual CSV raw-ingestion design, geography/ownership strategy review, documentation updates, and Git/GitHub workflow support | Official BLS QCEW source checks, raw sample creation, temporary SQLite ingestion tests, idempotency checks, unittest discovery, and Git diff review |

## Assignment 4 Student-Directed Decisions

For the Assignment 4.1 planning stage, student-directed architectural decisions include:

- using segmented Assignment 4 development instead of one large implementation
- retaining reference, raw, staging, intermediate, analytics, and model-ready data layers
- preserving iterative versions rather than overwriting source data
- using a hybrid API/bulk-file acquisition approach
- establishing a canonical clean analytical dataset
- prioritizing auditability and traceability

No substantive AI suggestion was rejected or corrected during this A4.1 setup step. This disclosure should be updated in a later Assignment 4 segment when there is a genuine AI suggestion that the student corrects or rejects.

## Assignment 4.2 Student-Directed Decisions

For the Assignment 4.2 schema stage, student-directed design decisions include:

- retaining the layered architecture from A4.1
- preserving raw, staging, intermediate, analytics, and metadata/quality versions rather than overwriting source data
- using `MSA x 2-digit NAICS x year` as the final analytical grain
- using 2010-2023 as the primary Assignment 4 study window
- using SQLite and Python's standard `sqlite3` library for transparency and reproducibility
- keeping fold-specific entrepreneurial-gap construction out of the database to avoid modeling leakage

No substantive AI suggestion was rejected or corrected during this A4.2 schema step. This disclosure should be updated in a later Assignment 4 segment when there is a genuine AI suggestion that the student corrects or rejects.

## Assignment 4.3 Student-Directed Decisions

For the Assignment 4.3 reference and metadata stage, student-directed implementation decisions include:

- seeding only deterministic `ref_year` values for 2010-2023
- registering only the four approved source systems: BDS, QCEW, CBP, and ACS
- leaving source endpoint URL fields null until source-specific ingestion verifies the exact official access paths
- adding metadata helpers for manifests, pipeline runs, table metrics, and rejected records before live ingestion begins
- testing with temporary SQLite databases and synthetic metadata records only

A substantive AI-assisted path was corrected during this step: geography and NAICS/industry reference rows were not manually populated from memory or generic assumptions. That idea was rejected because those tables need authoritative CBSA/geography and NAICS source references or crosswalks to preserve auditability and avoid false joins.

## Assignment 4.4 Student-Directed Decisions

For the Assignment 4.4 authoritative reference stage, student-directed implementation decisions include:

- using official Census CBSA delineation and NAICS reference files rather than unofficial lists
- selecting the July 2023 CBSA delineation as a fixed geography vintage for later source mapping
- adding a county-to-CBSA crosswalk table because county membership has a different grain from CBSA geography
- using the 2022 NAICS structure as the analytical reference version while preserving 2012/2017/2022 concordance files for later mapping
- not applying speculative NAICS crosswalk mappings before source-native NAICS versions are verified
- testing reference loading in temporary SQLite databases rather than writing to the project database

A substantive AI-assisted shortcut was rejected during this step: simplified manually curated MSA or 2-digit NAICS lists were not used. The student-directed standard was to preserve official source files, checksums, manifests, and documented vintage/version choices before any BDS, QCEW, CBP, or ACS ingestion begins.

## Assignment 4.5 Student-Directed Decisions

For the Assignment 4.5 BDS raw-ingestion stage, student-directed implementation decisions include:

- using official Census BDS sources only
- choosing the bulk CSV source family over the API because BDS API data calls require a key and bulk files are directly reproducible
- committing only a small permitted sample from the official BDS MSA-by-sector bulk file rather than the full national raw file
- preserving source-native `msa`, `sector`, `year`, measure values, and `D`/`N`/`S`/`X` status values in the raw payload
- avoiding source-to-reference geography or NAICS mapping until A4.6
- testing BDS raw ingestion in temporary SQLite databases

A substantive AI-assisted shortcut was rejected during this step: BDS `msa` and `sector` values were not mapped directly to the July 2023 CBSA and 2022 NAICS standards. The student-directed decision was to preserve native BDS coding first and require explicit mapping review before staging or entrepreneurship-measure construction.

## Assignment 4.6 Student-Directed Decisions

For the Assignment 4.6 BDS standardization stage, student-directed implementation decisions include:

- treating BDS native sector coding as 2017 NAICS, not 2022 NAICS
- preserving combined sectors such as `31-33` and `44-45`
- validating sector comparability against the 2022 NAICS reference rather than applying a blanket conversion
- defining startups from BDS firm-age-coarse age-0 firms
- constructing startup-rate lags only after geography and industry standardization
- requiring calendar-year continuity for lag construction
- retaining unresolved or suppressed rows in staging while excluding unusable rows from intermediate construction

A substantive AI-assisted shortcut was rejected during this step: blanket 2017-to-2022 NAICS conversion was not used. The student-directed decision was to validate comparability sector by sector and preserve source-native BDS sector codes and combined-sector conventions.

## Assignment 4.7 Student-Directed Decisions

For the Assignment 4.7 QCEW raw-ingestion stage, student-directed implementation decisions include:

- using official BLS QCEW annual CSV open data only
- preferring full-scale annual by-area bulk files for later production acquisition
- committing only a small official area-slice sample rather than the large annual national files
- preserving native `area_fips`, `own_code`, `industry_code`, `size_code`, annual measure fields, and disclosure/status fields in `raw_qcew`
- recommending county-level QCEW aggregation to the fixed July 2023 CBSA standard before analytical use
- recommending private-sector ownership, `own_code = 5`, for the later industry-growth panel unless a later research decision changes the scope
- deferring `stg_qcew`, growth calculations, lags, and industry standardization to A4.8

A substantive AI-assisted shortcut was rejected during this step: QCEW MSA-area rows were not treated as automatically equivalent to the project's July 2023 CBSA reference. The student-directed decision was to preserve native QCEW area codes in raw ingestion and require county-to-CBSA aggregation or explicit mapping review before standardization.
