# A7.8B UX and Plain-Language Refinement

## Executive summary

The dashboard presentation has been refined for clearer navigation, a dark-first theme with a native light-theme option, question-led page headings, and plain-language metric and coverage explanations. Technical names, formulas, caveats, and audit details remain available in context or in expanders. Changes are limited to the user interface, documentation, and tests; frozen A7.2/A6 values and model outputs are not changed.

## User feedback and design decisions

- Keep the Overview concise and lead with the retrospective result rather than methodology.
- Use familiar navigation labels while preserving existing route paths.
- Pair short metric labels with their technical names and definitions.
- Describe coverage as data completeness, never as prediction confidence.
- Preserve the distinction between historical model scores and live forecasts.

## Theme and navigation

The app defaults to a dark, high-contrast green-charcoal theme and defines a coordinated light theme using Streamlit's built-in theme selector. Plotly figures use the active Streamlit theme. Navigation labels are Overview, Explore Markets, Model Insights, Data & Confidence, and About the Analysis; route paths remain unchanged.

## Plain-language policy

Page headings are questions and introductory copy is brief. Visible labels favor familiar language; technical metric names and canonical codes remain accessible in help text, tables, and technical expanders. Coverage and model confidence are explicitly distinguished. Scores are described as retrospective and probabilistic, not as deterministic forecasts, causal findings, or policy recommendations.

## Page refinements

- **Overview:** Shorter KPI labels, direct performance and calibration explanations, retrospective status, plain coverage labels, and technical metric definitions in an expander.
- **Explore Markets:** Simpler filters and output labels while preserving canonical values and exact filters.
- **Model Insights:** Question-led sections and plain interpretations alongside technical score names and directionality.
- **Data & Confidence:** Plain coverage and missing-value language, with selection, suppression, and lineage detail retained.
- **About the Analysis:** Navigation and page introduction use the new product language; detailed methods remain intact.

## Technical detail preservation

Average Precision (AP), ROC-AUC, Brier score, lift, calibration, Logistic regression, and HistGradientBoosting remain named. Their definitions, directions, evaluation design, threshold detail, canonical coverage codes, and source/audit lineage remain available. No target, model fit, score, metric value, threshold, eligibility rule, or coverage rule was modified.

## Accessibility and responsive review

The theme specifies foreground/background colors and borders; status is conveyed with text, not color alone. Controls use Streamlit-native widgets, and chart layout avoids fixed white surfaces. Manual browser inspection covers the desktop viewport and the dark theme. This pass is not a WCAG conformance certification; narrow viewport simulation was unavailable in the connected browser controls.

## Verification

The full suite passes (190 tests); dashboard artifact health passes; `uv lock --check` resolves 155 packages without lock changes; and `git diff --check` passes. Browser review confirmed the Overview, Explore Markets, Model Insights, and Data & Confidence routes in dark mode, plus the light theme. Desktop viewport only was visually inspected; narrow viewport simulation was unavailable through the connected browser controls. The local application is served at `http://localhost:8772/` for review. Deployment and subsequent A7.9/A7.10 work remain out of scope pending user review.
