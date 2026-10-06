# Assignment 7 Risk Presentation Policy

## Primary Quantity

The raw frozen logistic predicted probability is the primary quantitative risk output. Display it as a percentage to one decimal place and retain the unrounded score in downloaded data/detail where useful. State the model and prediction horizon alongside it.

## Presentation Categories

“Lower predicted risk,” “Moderate predicted risk,” and “Higher predicted risk” are communication aids only. Before implementation, A7.2 must document a deterministic category rule and lineage (for example, fixed score bands or a frozen development-derived rule). The rule must not be selected, calibrated, or tuned to maximize holdout metrics, balance prevalence, or reach desired counts. These categories are not validated intervention, funding, or service thresholds.

A7.2 did not freeze such a rule. Its datasets therefore contain only continuous probability/rank, with no `risk_category`. Any later category decision is deferred to a separately reviewed A7.3/A7.4 presentation decision and must comply with the no-holdout-tuning rule below.

If a defensible fixed rule has not been documented, display probability and rank only; do not invent category cutpoints in the UI. Do not reuse the classifier's diagnostic threshold as an operational boundary without explicit rationale and disclosure.

## Language

Prefer: “predicted probability of a gap at t+3,” “higher predicted risk,” “eligible comparison,” and “observed gap in the later target year.” Avoid deterministic or stigmatizing language: “will fail,” “safe,” “dangerous,” “successful,” “failing,” “weak ecosystem,” or “economic failure.”

Every risk view states that results are model-relative, historical, conditional on complete-case eligibility, and not causal. Do not imply equal reliability across MSAs/sectors or invent confidence intervals. Show coverage/support caveats close to the score.

## Time and Target Roles

For a forecast pair, display predictor year `t` separately from target year `t+3`. Actual holdout gap is a realized future outcome used for retrospective evaluation; do not show it as information available at predictor time. Final holdout probabilities are evaluation artifacts, not evidence of deployment-time calibration or a live forecasting service.
