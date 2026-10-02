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
