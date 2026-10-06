# Assignment 7 Dashboard Plan

| Stage | Scope | Status |
| --- | --- | --- |
| A7.1 | Dashboard Architecture & User Requirements | Complete: audience, page architecture, UX, contracts/lineage, risk and visualization policies, wireframes, component inventory, map deferral. |
| A7.2 | Dashboard Data Layer | Complete: typed Parquet datasets, pure-Python loader, source/field lineage, coverage and null policies, quality checks, reproducibility audit, and documentation. |
| A7.3 | Core Streamlit Application Shell | Complete: five-page st.navigation shell, shared components/theme, Explorer-only filter state, cached A7.2 loader adapters, health CLI, and smoke-tested app. |
| A7.4 | Executive Overview | Complete: A7.2-only source-driven KPIs, Plotly holdout comparison/lift/calibration, retrospective top-N cases, gap explainer, practical interpretation, and limitations. |
| A7.5 | Regional & Industry Explorer | Complete: Explorer-only MSA/sector/year/gap/prediction filters, source-faithful historical views, separate development/holdout predictions, logistic rankings, coverage and empty states, and filtered CSV export. |
| A7.6 | Model Performance & Diagnostics | Complete: fixed A7.2 metrics, split/model comparisons, deterministic PR/ROC display curves, calibration, lift, time/MSA-size/sector diagnostics, interpretation, and source-lineage tests/report. |
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

A7.2 was completed as a separate stage after schemas and null/time-role rules were reviewed. The dashboard remains a descriptive/prioritization aid with no causal claim.

## A7.3 Exit Criteria

- Five approved page routes render from the Streamlit shell with only structural placeholder content.
- Shared layout/components/theme and Explorer-only filters use the A7.2 loader/options and preserve fixed A6 performance populations.
- Missing/corrupt/incompatible artifacts produce actionable health results; CLI and app startup checks pass.
- Focused shell tests, full suite, and bounded application smoke test pass; no model fitting, target reconstruction, chart, map, or deployment work is added.

A7.3 was completed without final Executive Overview visualizations or substantive analytics; A7.4 implements those items as its own stage.

## A7.4 Exit Criteria

- Executive Overview consumes only validated A7.2 artifacts; no SQLite reads, target reconstruction, or model refitting.
- Final holdout metrics, lift, calibration, and ranked cases remain retrospective and use the pre-locked logistic primary model; HGB remains sensitivity only.
- The page explains the entrepreneurial-gap construction, what the score can and cannot support, and sample coverage and limitations without inventing risk bands.
- Plotly charts, top-N output, focused tests, full test suite, and bounded browser smoke check pass.
- App guide, AI-use disclosure, and A7.4 implementation report are updated; later A7 stages remain untouched.

A7.4 is complete; A7.5 was implemented and verified as a separate stage below.

## A7.5 Exit Criteria

- Explorer uses only validated A7.2 panel, prediction, filter-option, label, and metadata artifacts; keys and exact t+3 pairs are validated.
- MSA, sector, descriptive year, observed-gap and evaluation-prediction availability filters use documented defaults and reset behavior; risk categories remain unavailable.
- Observed/expected rates, startup and employment trends, alignment, historical A6 gap labels, and retrospective prediction scores remain distinct by source and time role; nulls are never replaced or extrapolated.
- Development OOF and final holdout prediction views are explicitly separated; logistic remains primary and rankings sort by its frozen probability.
- Coverage, data availability, empty states, contextual limitations, and filtered CSV metadata are present.
- Focused and full tests, dashboard health checks, representative QA cases, and bounded Explorer smoke testing pass.
- App guide, AI-use disclosure, and A7.5 report are updated. A7.6 and later stages remain incomplete.

A7.5 is complete. The Regional & Industry Explorer remains descriptive and retrospective; A7.6 is documented as a separate stage below.

## A7.6 Exit Criteria

- Performance page validates and consumes only finalized A7.2 metrics, calibration, year, MSA-size, sector, prediction, metadata, and label artifacts; fixed metrics remain independent of Explorer state.
- Logistic remains primary, HGB remains sensitivity, and Random Forest appears only if a finalized comparison metric exists. Development OOF and final temporal holdout stay explicitly separate.
- PR/ROC points, when shown, are a deterministic display-only transform of unchanged frozen probability/actual-label pairs, with no model fit, threshold selection, or summary-metric recomputation; lineage and this narrow contract allowance are documented.
- Calibration and lift use fixed A7.2 values; temporal/size/sector diagnostics preserve source sample counts and sector sufficiency suppression. Metric direction and interpretation are explicit.
- Focused and full tests, dashboard health, lockfile/diff checks, cross-page reconciliation, and bounded browser smoke pass; the A7.6 report and app guide are updated.
- A7.7 through A7.10 remain incomplete. No Data Quality page, map, deployment, retraining, or A7.7 work is included.

A7.6 is complete. Stop after this stage; A7.7 Data Quality, Coverage & Limitations remains a separate next assignment.
