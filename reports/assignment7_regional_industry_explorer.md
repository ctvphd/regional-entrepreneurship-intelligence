# Assignment 7.5 Regional & Industry Explorer

## Executive Summary

The Explorer is implemented as an interactive, retrospective view over
validated A7.2 panel and prediction artifacts. It adds MSA/sector/year/gap and
prediction-availability filters, source-faithful history charts, exact-key
prediction details, logistic-primary rankings, A5 coverage context, clear
empty states, and filtered CSV export. No model, target, expected value,
cutpoint, or prediction is recomputed. No map or A7.6 page work was added.

## Purpose and Filters

The page helps users inspect historical startup activity, A6 expected startup
activity, alignment, development fold-validation gap labels, and finalized
future-gap evaluation predictions. Explorer filters do not change fixed
Executive Overview or Model Performance evaluation populations.

- Searchable MSA selector; no MSA is preselected.
- Sector multiselect; empty means all observed sectors.
- Descriptive year selector; default is the latest panel year, 2023.
- Historical A6 gap status selector; default is all.
- “Only rows with an evaluation prediction” checkbox; default off and matched
  on exact CBSA-sector-predictor-year keys.
- Risk-category selector remains disabled because A7.2 defines no approved
  presentation bands.
- Prediction ranking separately selects `final_holdout` or `development_oof`,
  predictor year, and top 10/25/50. The default is final holdout, 2020, top 10.

Reset restores all MSAs, all sectors, latest descriptive year, no gap or
prediction-only filter, final holdout, its latest predictor year, and top 10.

## Key Metrics and Charts

For a single MSA-sector-year, metric cards show observed startup rate, expected
startup rate, alignment in startup-rate percentage points, historical A6 gap
status, logistic probability at t+3 when the exact predictor pair exists,
employment growth, and A5 coverage status. Broad selections never average
these across unrelated MSA-sector rows. Missing values display as `N/A` with
their availability context; no missing value is replaced with zero.

Plotly views include:

- Observed versus expected startup-rate history, with a dashed expectation
  series and distinct historical-gap markers.
- Observed startup-rate trend and a separate decimal-rate employment-growth
  trend.
- Alignment history with a zero reference; negative values mean observed
  activity was below expectation. No A6 threshold is reconstructed.
- Historical A6 gap timeline, explicitly labeled as development OOF target
  labels, not future probabilities.
- Logistic probability history for one explicitly selected evaluation split,
  with predictor and target years in hover text.

Dynamic takeaways use only filtered values. Startup rates retain source percent
units, employment growth is formatted as a percent, and alignment is shown in
percentage points. Symbols as well as color distinguish observed gap markers.

## Prediction Semantics and Ranking

Predictions are joined only on MSA, sector, and predictor year. Every record
is validated for an exact metadata-defined t+3 target, unique key, approved
evaluation split, approved coverage status, binary actual outcome, and
probability bounds. A 2020 predictor-year score therefore identifies the
2023 target; it is not a current forecast.

The ranking uses the frozen logistic probability descending and applies the
selected MSA/sector filters. Development OOF and final holdout are selected
separately and never mixed in one ranking. Actual target gaps are labeled
retrospective. HistGradientBoosting remains secondary and is not offered as a
co-primary ranking toggle.

## Coverage, Empty States, and CSV

Coverage displays only the A5 statuses `comparison_eligible` and `thin` with
the 100-row/5-sector/10-year rule. Thin MSAs remain selectable and receive a
contextual caution; status does not imply model confidence.

Empty states cover no selected panel rows, no expected rate, no A6 alignment
or historical gap record, no prediction for the selected MSA-sector/split,
unavailable employment growth, and no panel history under active filters.
Time roles remain visible and nulls are not extrapolated.

The UTF-8 CSV reflects the MSA, sector, descriptive-year, gap, and
prediction-availability filters. It exports only dashboard panel fields plus
exact-key prediction fields where present, dashboard version, and primary
model context. Predictor and target years are distinct columns; actual target
gap is explicitly retrospective. The visible preview is capped at 100 rows;
the download contains all matching filtered rows. No raw or staging sources
are included.

## Accessibility and Performance

Controls use searchable/native Streamlit selection widgets with help text.
Charts have descriptive titles, axes and units, gap symbols beyond color, and
short dynamic text takeaways. Tables expose human-readable MSA/sector labels
and a clear empty state. App reads are cached; filtering and key joins are
vectorized. In a local check, selecting one MSA-sector-year from the 63,577-
row panel took 0.02 seconds; attaching the 23,937-row prediction artifact to
the panel took 0.03 seconds. These are local data-operation timings, not a
deployment latency guarantee.

## QA Cases

- **Broad eligible MSA:** New York-Newark-Jersey City (CBSA 35620) has 178
  panel rows, 14 sectors, 14 years, and `comparison_eligible` status. Retail
  Trade has A6 expected/alignment/gap records for 2017-2020. Its 2020
  holdout score is 9.9% for the 2023 target; the observed target gap is 0.
- **Thin MSA and unavailable values:** Atlanta-Sandy Springs-Roswell (CBSA
  12060) has 65 rows, 6 sectors, and 14 years, so its A5 status is `thin`.
  Construction (sector 23) has a 2013 observed startup-rate row but no A6
  expected rate, alignment, gap label, or final holdout prediction. The page
  retains the observed rate, shows the thin warning, and renders explicit
  expected/alignment/prediction empty states.
- **Major MSA with incomplete sector support:** Chicago-Naperville-Elgin
  (CBSA 16980) has 95 rows, 11 of the 19 sectors, and 14 years. Filtering
  retains those 11 observed sectors and does not create missing sector rows.
- **Unusual observed rate:** Bay City, MI, Agriculture (CBSA 13020, sector
  11, 2015) retains the source startup rate of 80.0 percent units, while the
  expected rate remains unavailable; no clipping or expectation is invented.

AppTest exercised MSA, sector, descriptive year, gap-status, prediction
availability, prediction split/year, Top N, reset, charts, and the CSV control.
The bounded browser smoke reached `/explorer`, rendered the default ranking,
filter panel, coverage summary and export control, and the server was stopped
after QA.

## Verification

- Focused Explorer tests: 11 passed.
- Dashboard health CLI: PASS for all required A7.2 artifacts and metadata.
- Full test suite: 161 passed; 0 failures, 0 errors, 0 skips.
- `uv lock --check` and `git diff --check`: PASS.
- The canonical analytical database and A7.2 dashboard artifact files were
  read only; no model fitting, dataset regeneration, map, deployment, or A7.6
  implementation occurred.

## Readiness for A7.6

A7.5 is complete. The Explorer makes the source data's null, time-role,
coverage, and holdout boundaries visible. A7.6 Model Performance &
Diagnostics can proceed as a separate stage; this report does not implement
or preview that page.
