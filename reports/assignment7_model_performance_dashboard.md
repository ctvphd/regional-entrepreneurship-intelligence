# A7.6 Model Performance & Diagnostics

## Executive Summary

The fixed Model Performance page is implemented from validated A7.2 artifacts.
It presents final-holdout results, Development OOF comparisons, deterministic
PR/ROC display curves, calibration, lift, target-year variation, MSA-size
variation, and sector performance with source sufficiency suppression intact.
The frozen logistic model remains primary; HistGradientBoosting remains a
sensitivity comparison. No model was fit or changed.

## Page Purpose

The page answers how the locked model ranked later gap outcomes and how those
results vary across the fixed evaluation split, target years, MSA-size groups,
and sectors. It is not filtered by Explorer state. Final holdout target labels
are retrospective evaluation outcomes, not current forecasts.

## Primary Metrics

Final temporal holdout logistic results (10,304 pairs; prevalence 0.233):

| Metric | Value | Interpretation |
| --- | ---: | --- |
| Average Precision | 0.404 | Above the 0.233 holdout prevalence reference; ranking signal, not accuracy. |
| ROC-AUC | 0.692 | Above 0.500 random-ranking reference. |
| Brier score | 0.164 | Mean squared probability error; lower is better. |
| Recall | 0.708 | At the frozen A6 diagnostic threshold. |
| Precision | 0.328 | At the same frozen threshold. |
| F1 | 0.448 | Threshold-specific harmonic mean. |
| Top-decile lift | 1.99x | Top-ranked tenth had about 1.99 times the overall gap prevalence. |

These values come from `dashboard_model_summary`, and reconcile to the
Executive Overview. The displayed prevalence is 23.3%; N is 10,304.

## Development vs Holdout

| Split | N | Prevalence | AP | ROC-AUC | Brier | Top-10 lift |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Development OOF | 13,633 | 0.191 | 0.367 | 0.693 | 0.142 | 2.25x |
| Final temporal holdout | 10,304 | 0.233 | 0.404 | 0.692 | 0.164 | 1.99x |

Holdout AP is higher than Development OOF in these fixed samples; ROC-AUC is
nearly unchanged, Brier is worse, and top-decile lift is lower. These values
are descriptive of one temporal holdout, not proof of external or universal
generalization. Pooled Development OOF's published fold-specific prevalence
benchmark AP (0.183) is not identical to pooled prevalence (0.191); the
published A6 benchmark value is retained without substitution.

## Model Comparison

| Model | Split | AP | ROC-AUC | Brier | Top-10 lift |
| --- | --- | ---: | ---: | ---: | ---: |
| Prevalence benchmark | Holdout | 0.233 | 0.500 | 0.180 | 1.00x |
| Logistic regression (primary) | Holdout | 0.404 | 0.692 | 0.164 | 1.99x |
| HistGradientBoosting (sensitivity) | Holdout | 0.424 | 0.708 | 0.161 | 2.09x |

HGB has modestly higher holdout ranking scores and a slightly lower Brier
score. Logistic remains primary because it is the pre-locked, more
interpretable and stable reference specification; HGB did not justify a
post-hoc model switch. Random Forest is
not in the frozen A7.2 summary and is therefore not shown; the page supports
comparison-only display if finalized development metrics become available.

## Precision-Recall

Curves are constructed from unchanged finalized probabilities and `actual_gap`
within a single selected split. The horizontal no-information reference is
the split's prevalence. Holdout logistic AP (0.404) exceeds holdout prevalence
(0.233). AP is the primary metric for the minority gap class; it is not
traditional accuracy. The dashboard does not recalculate the published AP.

## ROC

ROC coordinates use the same frozen score/outcome pairs and split separation.
The chart includes a random-ranking diagonal; 0.500 represents random
discrimination. ROC-AUC need not exceed 0.800 to represent useful signal and
must be read alongside AP, calibration, and lift.

## Calibration

The reliability chart uses published `dashboard_calibration` bins and an
ideal 45-degree reference. In the final-holdout logistic bins, observed gap
prevalence is above the mean predicted score in 7 of 10 bins and below it in
3; this describes bin-level under/overprediction without smoothing or
recalibration. Points do not establish behavior between bins.

## Lift

Frozen holdout logistic lift is 1.99x in the top 10%, 1.75x in the top 20%,
and 1.66x in the top 25%. HGB sensitivity values are 2.09x, 1.84x, and 1.74x.
The table shows selected N using the A6 ceiling-of-fraction rule; observed
prevalence is presented as frozen lift multiplied by frozen overall
prevalence. No row-level performance metric is recomputed.

## Temporal Stability

Logistic final-holdout metrics vary by target year:

| Predictor to target | N | Prevalence | AP | ROC-AUC | Brier |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2018 to 2021 | 3,372 | 0.243 | 0.435 | 0.710 | 0.167 |
| 2019 to 2022 | 3,432 | 0.181 | 0.355 | 0.695 | 0.137 |
| 2020 to 2023 | 3,500 | 0.273 | 0.427 | 0.671 | 0.187 |

AP is lowest in the 2019-to-2022 pair, ROC-AUC is lowest in 2020-to-2023,
and Brier is highest (worse) in 2020-to-2023. Holdout targets fall in
pandemic/post-pandemic years; these year patterns are descriptive and do not
identify pandemic effects.

## MSA-Size Performance

Logistic AP is 0.462 for small, 0.395 for middle, and 0.348 for large MSA-size
groups. ROC-AUC is 0.662, 0.651, and 0.736, respectively; top-decile lift is
1.81x, 1.79x, and 2.29x. Each group has fixed sample counts in the chart
hover. Differences may reflect both model behavior and sample composition.

## Sector Performance

The sector table includes sector, N, positive N, prevalence, AP, ROC-AUC, and
the source `sufficient_sample_flag`. Seventeen logistic sectors are flagged
sufficient and two are not. Utilities (169 observations, 3 positives) and
Management of Companies and Enterprises (196 observations, 11 positives)
retain blank AP/ROC-AUC as suppressed in A6. The AP chart includes only
sufficient sectors and reports N/prevalence on hover. Sector importance as a
predictor does not imply uniformly strong within-sector performance.

## Metric Glossary

The page defines prevalence, AP, ROC-AUC, Brier, recall, precision, F1, lift,
and calibration in practical language. It identifies higher/lower-is-better
directions, distinguishes threshold metrics from ranking metrics, and warns
against rigid ROC-AUC cutoffs.

## Accessibility

Model comparisons keep metric families and direction separate. Logistic and
HGB are differentiated by color plus pattern/line type/marker; the random
reference is separately styled. Charts include units, split/time roles,
sample-size hover context, and text summaries. Sector sufficiency is shown in
both a chart restriction and a full table flag; color is not the only cue.

## Cross-Page Reconciliation

Executive Overview and Performance both read the same A7.2 long-form summary.
Holdout AP 0.404, prevalence 0.233, ROC-AUC 0.692, Brier 0.164, and top-decile
lift 1.99x match. Explorer and Performance both label 2020-to-2023 as a
retrospective t-to-t+3 evaluation, not a current forecast. The same primary
logistic and HGB sensitivity labels are used across pages.

## Verification

- Baseline before A7.6: 161 tests passed.
- Focused A7.6 suite: 11 tests passed after final implementation.
- Full suite after A7.6: 172 tests passed; failures 0, errors 0, skips 0.
- Dashboard health passed for every required A7.2 JSON/Parquet artifact;
  `uv lock --check` and `git diff --check` passed.
- Bounded live browser smoke rendered `/performance` without a traceback and
  visibly verified the metric cards, comparison tabs, PR/ROC/calibration,
  lift table, year chart, MSA-size chart, and sector chart/table.
- Curve lineage is documented in `docs/ASSIGNMENT7_SOURCE_LINEAGE.md` and the
  display-only permission is explicit in `docs/ASSIGNMENT7_DATA_CONTRACTS.md`.

## Readiness for A7.7

A7.6 is complete. No Data Quality page, map, deployment, retraining, or A7.7
work was included. A7.7 remains the next distinct stage.
