# Assignment 7.4 Executive Overview Implementation Report

## Scope

The default Executive Overview now presents the frozen A6 results through the
validated A7.2 dashboard layer. The page does not read SQLite, reconstruct the
target, refit a model, alter the holdout, or create risk bands. Logistic
regression remains the pre-locked primary model; HistGradientBoosting remains
a sensitivity model. The other A7 pages remain within their planned stages.

## Results Shown

The primary holdout KPIs are sourced from `dashboard_model_summary.parquet`:

| Measure | Final temporal holdout |
| --- | ---: |
| Average Precision | 0.404 |
| Gap prevalence | 23.3% |
| ROC-AUC | 0.692 |
| Brier score | 0.164 |
| Top-decile lift | 1.99x |
| Prediction pairs | 10,304 |
| MSAs represented | 365 |
| Two-digit NAICS sectors | 19 |

Development OOF versus holdout values are displayed from the same artifact:
AP 0.367 versus 0.404, ROC-AUC 0.693 versus 0.692, and Brier 0.142 versus
0.164. The page states that lower Brier is better. Holdout lift at the top
10%, 20%, and 25% is approximately 1.99x, 1.75x, and 1.66x. The calibration
plot uses final-holdout logistic score bins; observed prevalence runs from
4.2% in the lowest bin to 46.1% in the highest. These remain retrospective
evaluation summaries, not recalibration or live predictions.

HistGradientBoosting's holdout AP and ROC-AUC exceed logistic by 0.020 and
0.017, respectively. This post-lock sensitivity comparison does not replace
the preselected logistic primary model.

## Data and Interpretation

`overview_data.py` validates A7.2 metadata, required metric rows, holdout
sample reconciliation, exact forecast horizon, calibration and subgroup
presence, coverage and source metadata before display. `charts.py` builds the
development/holdout comparison, holdout lift, calibration, and stable ranked
case table. The table selector offers top 10, 25, or 50 cases and labels the
actual target status as retrospective, using A7.2's gap-status labels.

Page text explains the Model A expected-startup benchmark and development-only
p20 gap threshold, along with intended prioritization use and non-causal,
non-prescriptive limitations. Coverage is reported only with the approved
`comparison_eligible` and `thin` values. The source strip is filtered against
the source artifact and reports Census BDS, BLS QCEW, Census ACS, and Census
CBP.

## Verification

- Focused Executive Overview tests: 6 passed.
- Dashboard health CLI: PASS for all required A7.2 artifacts and metadata.
- Full test suite: 150 tests passed.
- Bounded Streamlit browser smoke on port 8767: Overview loaded; KPI values,
  comparison/lift/calibration charts, top-10 selector and table, gap explainer,
  coverage disclaimer, and source links were present. Server was stopped after
  the check.
- Streamlit layout calls use `width="stretch"`; the page-specific deprecation
  warning was removed.
- No A7.5+ work was started.

## Limitations

The single temporal holdout does not establish external or universal
generalization. Complete-case selection is patterned, the unit is a two-digit
NAICS sector within an MSA, and firm startup rates represent a narrower
entrepreneurship construct. Model scores are not causal effects, guarantees,
or funding recommendations. Holdout cases are retrospective and must not be
treated as current forecasts.
