# Assignment 7 Visual QA Checklist

Use for the implemented Executive Overview, Regional & Industry Explorer, Model Performance, and Data Quality & Limitations routes.

## Per-chart checks

- [ ] Descriptive title is visible; short context and takeaway sit outside the plot where useful.
- [ ] Axes state metric, time role, and units; no unexplained truncation.
- [ ] Legend text is human-readable; logistic is primary and HGB sensitivity is secondary.
- [ ] Development OOF and Final temporal holdout are named consistently.
- [ ] Metric direction is explicit: higher is better for AP/ROC-AUC/recall/precision/F1/lift; lower is better for Brier.
- [ ] Hover uses human-readable labels, useful units, MSA/sector/year context when row-level geography applies, and no excess decimals.
- [ ] Meaning is not color-only; marker/line/pattern/text cues distinguish observed/expected, gap/no-gap, and sufficiency.
- [ ] Nulls, suppression, sample support, and retrospective target outcomes remain explicit.
- [ ] Values and chart coordinates trace to the approved A7.2/A6 sources; no science is recomputed.

## Tables and layout

- [ ] Column labels are readable; counts, percentages, scores, lifts, and years follow the shared precision policy.
- [ ] Sorting/search and sample/coverage flags remain available where appropriate.
- [ ] Desktop/laptop/narrow-window review checks clipping, legibility, legend wrap, and table width.
- [ ] Long diagnostic sections are grouped without hiding core results behind excessive clicks.

## Cross-page boundary checks

- [ ] Shared glossary and canonical split labels are used; logistic remains primary, HGB remains sensitivity.
- [ ] Actual future outcomes are labeled retrospective, never current or live forecasts.
- [ ] No SQLite/raw-data access, target/model change, map, deployment, or static A5/A6 figure redesign.
- [ ] Focused and full test suites, dashboard health, lockfile check, diff check, and route smoke pass.

This checklist is a manual/automated review aid, not a formal WCAG conformance claim.
