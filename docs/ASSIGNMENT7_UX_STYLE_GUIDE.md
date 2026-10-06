# Assignment 7 UX Style Guide

## Brand Tone

Professional, analytical, restrained, and approachable. The interface should
feel like a reliable research product, not a game or a marketing page.

## Writing Tone

Plain language first; exact technical detail second. Use concrete verbs and
short sentences. State when evidence is historical, model-relative, incomplete,
or non-causal.

## Page Titles

- Overview: “Where are startup gaps emerging, and can we spot patterns early?”
- Explore Markets: “How is startup activity changing across places and industries?”
- Model Insights: “How well does the model identify future gaps?”
- Data & Confidence: “Where is the evidence strongest, and where should we be cautious?”
- About the Analysis: “How was this analysis built?”

## Section Headings

Use a question or user task: “Did the results hold up on later data?” rather
than “Temporal validation diagnostics.” Put the methodology in a subtitle or
technical expander.

## Metric Naming

Pair a plain headline with the exact metric name and concise interpretation.
Never hide statistical names. Brier score always says lower is better; AP is
compared with observed prevalence; ROC-AUC describes ranking; lift compares a
selected share with the overall rate.

## Card Patterns

Use Streamlit bordered containers for a small number of important KPI or status
cards. Each has one short headline, one primary value, an exact technical label,
and a concise interpretation. Avoid nesting cards or framing every paragraph.

## Chart Titles

Use a user question or a direct finding. Preserve metric names, units, years,
and category meanings in axes, legends, captions, or hover details. Add one
short nearby sentence explaining why the chart matters.

## Tooltip Conventions

Explain the exact metric or field, its unit, time role, and important caveat.
Technical terms are welcome when defined in the same help text.

## Coverage Wording

Use “Good comparison coverage” and “Limited data coverage” in primary copy.
Retain the canonical source values `comparison_eligible` and `thin` in help or
technical detail. Coverage is not confidence or a grade for a place.

## Gap Wording

Use “Gap observed,” “No gap observed,” and “Not available.” Explain that a gap
means startup activity was unusually low relative to the model's expected
benchmark. Do not describe a community as failing or weak.

## Model Wording

Logistic regression is the primary model. HistGradientBoosting is a sensitivity
check. Future gap risk is a retrospective three-year-ahead evaluation score,
not a current forecast or guarantee.

## Limitation Wording

Lead with who or what may be missing and the practical implication. Keep
selection rules, thresholds, sample counts, and technical caveats in an
expander or linked method note.

## Dark and Light Themes

Dark is the default: charcoal surfaces, warm light text, restrained teal
accent, and subtle borders. The native Streamlit theme selector provides the
configured light alternative. Plotly uses Streamlit's active chart theme;
semantic color meaning is also encoded through labels, markers, patterns, or
line style. Do not claim WCAG certification without formal testing.
