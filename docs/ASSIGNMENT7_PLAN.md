# Assignment 7 Dashboard Plan

| Stage | Scope | Status |
| --- | --- | --- |
| A7.1 | Dashboard Architecture & User Requirements | Complete: audience, page architecture, UX, contracts/lineage, risk and visualization policies, wireframes, component inventory, map deferral. |
| A7.2 | Dashboard Data Layer | Complete: typed Parquet datasets, pure-Python loader, source/field lineage, coverage and null policies, quality checks, reproducibility audit, and documentation. |
| A7.3 | Core Streamlit Application Shell | Incomplete; not started. |
| A7.4 | Executive Overview | Incomplete; not started. |
| A7.5 | Regional & Industry Explorer | Incomplete; not started. |
| A7.6 | Model Performance & Diagnostics | Incomplete; not started. |
| A7.7 | Data Quality, Coverage & Limitations | Incomplete; not started. |
| A7.8 | Interactive Visualization Refinement | Incomplete; not started. |
| A7.9 | Deployment & Containerization | Incomplete; not started. |
| A7.10 | Final Integration, QA & Completion | Incomplete; not started. |

## A7.1 Exit Criteria

- Requirements and audience jobs map to all five approved pages.
- Filter scope, display policy, risk vocabulary, lineage/contracts, accessibility, downloads, reproducibility, and success criteria are explicit.
- Five text wireframes and reusable component inventory exist.
- Future map requirements are documented as deferred.
- Existing A6 tests pass; no app, dataset, model, database, chart, map, container, or deployment implementation is added.

A7.1 established the architecture and boundaries; A7.2 implemented and validated the materialized data layer under those rules. Final holdout outcomes remain retrospective evaluation-only. The dashboard remains a descriptive/prioritization aid with no causal claim.

## A7.2 Exit Criteria

- Dashboard Parquet/JSON artifacts are built deterministically from the read-only A4 view and frozen A5/A6 outputs.
- Dataset keys, types, time roles, model metrics, prediction splits, coverage, nulls, and source lineage are validated and documented.
- Final holdout outcomes remain retrospective evaluation-only; no dashboard risk categories are introduced without a frozen non-holdout rule.
- A7.2 tests and the existing full test suite pass; the canonical SQLite database remains unchanged.
- No Streamlit UI, charts, maps, deployment, or A7.3 implementation is included.

Proceed to A7.3 only as a separate stage after reviewing the A7.2 contracts, schemas, and null/time-role rules. The dashboard remains a descriptive/prioritization aid with no causal claim.
