# Assignment 7 Dashboard Requirements

## Purpose

Present the completed regional entrepreneurship research clearly and let users explore historical MSA-by-industry patterns and the final, fixed-model future-gap evaluation. The dashboard is an exploratory and prioritization aid, not an intervention prescription, forecast guarantee, or causal analysis. Assignment 7 must display existing A6 results faithfully; it must not redesign or refit the models.

## Primary Audiences

- Economic-development practitioners and business-support organizations.
- Academic researchers and students.
- Policymakers and local-government staff.
- Entrepreneurs and ecosystem-support organizations.

## User Jobs-to-be-Done

| Audience | User goal | Guardrail |
| --- | --- | --- |
| Economic-development practitioner | Find higher-risk MSA-industry pairs, inspect observed versus expected startup activity, compare sectors, and review trends. | Treat ranking as a prompt for investigation, not a causal diagnosis or funding rule. |
| Researcher | Inspect validation metrics, target construction, provenance, coverage, and limitations. | Keep development and final-holdout populations and time roles explicit. |
| Policymaker | Understand where the model flags possible future gaps and how uncertain that signal is. | Predictions are probabilistic and may not generalize equally across places or sectors. |
| Entrepreneur/support organization | Explore regional and industry patterns where startup activity may lag the model-relative expectation. | Do not describe a sector or place as failing or deficient. |

## Primary Analytical Questions

- How does observed startup activity compare with expected startup activity for a place and sector?
- Which eligible MSA-sector observations had higher predicted future gap risk under the locked reference model?
- How do startup rate, employment growth, alignment, and observed gap status vary over time?
- How well did the frozen models rank and calibrate the reserved temporal holdout, and where are results limited?
- What coverage, selection, measurement, and generalization caveats apply to an observation?

## Scope

Five-page, light-theme, hybrid academic/professional experience: Executive Overview; Regional & Industry Explorer; Model Performance; Data Quality & Limitations; About / Methods / Sources. Initial delivery emphasizes interpretation, reproducibility, accessible interaction, and one filtered CSV download. Build only through the staged A7.2–A7.10 roadmap.

## Out of Scope

- Any model, research-question, target, threshold, or holdout change; causal recommendation; or deterministic failure claim.
- Full interactive map, new dashboard datasets in A7.1, PDF export, mandatory pairwise comparison, or dynamic walkthrough.
- A7.2 data-layer code, Streamlit pages, production Plotly charts, Docker, or deployment in this architecture phase.
- Replacing/deleting A5/A6 Matplotlib artifacts or redesigning publication figures before post-A7 refinement.

## Five-Page Architecture

### 1. Executive Overview

Lead with project title, one-sentence description, research question, unit/time period, and primary-model identification. Show final holdout AP (0.404), prevalence (0.233), ROC-AUC (0.692), top-decile lift (1.99x), and sample counts with the holdout label. Present development-versus-holdout comparison, risk-decile/lift story, a qualified top-risk table, and a plain-language gap explainer with a static example. Link to Explorer, Model Performance, and Limitations. Do not expose a filtered holdout ranking as current prospective advice.

### 2. Regional & Industry Explorer

Searchable MSA selector, sector multiselect, year, presentation risk category, and observed gap status. Show predicted future risk first when an eligible, temporally valid prediction exists, then observed-versus-expected startup activity, alignment residual/label, gap status, and coverage. Include observed/expected chart plus numeric summary, historical startup/employment-growth/alignment trends where sourced, and Top 10/25/50 eligible ranking. Distinguish predictor year from target/outcome year. Explorer controls do not change fixed Model Performance metrics.

### 3. Model Performance

Compare prevalence benchmark, primary logistic, and frozen HGB sensitivity; Random Forest appears only if fixed A6 artifacts support a useful, correctly labeled comparison. Show AP, ROC-AUC, Brier, recall, precision, F1, calibration, lift, precision-recall and ROC curves, risk bins, and development OOF versus holdout. Include year and MSA-size summaries. Explain AP relative to prevalence, why ROC-AUC below 0.80 is not automatic failure, why calibration matters, and why logistic remains primary. Technical detail goes in expanders; no view enables refitting or threshold tuning.

### 4. Data Quality & Limitations

Surface MSA/sector/year coverage, complete-case eligibility and patterned exclusions, missingness/suppression context, MSA-size and sector variation, and the finite temporal holdout. Use contextual warnings at observation and chart level. State that startup rate is narrower than entrepreneurship broadly, industries are 2-digit NAICS, the gap is relative to a fitted expectation, and prediction is not causal. Do not imply every geography/sector has comparable reliability.

### 5. About / Methods / Sources

Explain project purpose, sources, study period, MSA x 2-digit NAICS x year unit, expected-startup benchmark, residual/p20 target, exact t-to-t+3 horizon, model choices, robustness, holdout design, data dictionary, version metadata, and AI-use disclosure. Plain language comes first; formulas, eligibility logic, and source lineage are expandable. Attribute sources contextually and on this page.

## Navigation and Filter Scope

Use sidebar navigation, page title, and short page description. Persistent controls are appropriate for Explorer only. MSA, sector, year, risk category, and observed gap status apply to Explorer rows/charts/download. They must not filter or silently recompute Model Performance metrics, which are fixed A6 evaluation artifacts. Overview rankings state their fixed eligible universe or use explicitly scoped controls. Methods, sources, and limitations remain stable reference content.

## Model Display Rules

- Logistic is the primary/reference because it is interpretable and performs near the frozen HGB sensitivity.
- HGB is labeled sensitivity, never default or promoted based on holdout performance.
- Show natural-prevalence benchmark. Preserve official A6 values and dataset/sample labels; do not recompute metrics in the interface.
- Identify development OOF and 2021–2023 target holdout separately. One temporal holdout is not external validation.
- No model switch, retuning, calibration refit, or metric-derived operational cutoff in the dashboard.

## Risk Display Rules

Show raw frozen logistic probability as the primary quantitative value, formatted to one decimal percent; retain raw precision in accessible detail/tooltip if useful. “Lower/Moderate/Higher predicted risk” categories are presentation aids, not validated action thresholds. Their fixed derivation must be documented before implementation; never tune cutoffs on holdout. Pair risk with horizon, sample/coverage context, and uncertainty note. Never say an MSA-sector “will fail.”

## Download Behavior

Initial release supports filtered CSV export from Explorer only. Include only displayed eligible fields: CBSA code/name, sector code/title, predictor year, target year when a valid prediction exists, observed/expected startup activity and alignment when sourced, observed gap status with time role, logistic probability, presentation category, and coverage indicator. HGB score is optional and clearly labeled sensitivity. Do not export raw/source tables or imply a future outcome was known at predictor time. Deterministic filename: `regional_entrepreneurship_explorer_<year>_<date>.csv`. State active filters and definitions near the control. No PDF/report export initially.

## Data Quality Behavior

Show per-MSA/sector coverage context from audited sources, without inventing strong/moderate/thin rules until A7.2 documents deterministic definitions. Mark missing, suppressed, out-of-support, and ineligible observations distinctly; do not silently impute. Label metric denominators and suppress unstable subgroup metrics per A6 (fewer than 30 positive events or no class variation). Warn that complete-case selection is patterned, metro coverage varies, and predictive quality is not uniform. No confidence intervals without a valid prespecified method and source.

## Methodology Disclosure

Plain-language explanation by default and technical detail in expanders. Define model-relative entrepreneurial gap and give a numeric illustrative example. Distinguish observed startup activity, expected startup activity, alignment residual, current/realized gap label, predictor-time score, and later holdout outcome. State exact t+3 horizon, development/holdout dates, model-lock reference, no holdout tuning, no causal interpretation, and sources. Avoid long paragraphs beneath every chart.

## Accessibility and Visual Communication

Light theme; high contrast; readable type; keyboard-friendly native controls; descriptive chart titles, subtitles, axes, units, and one-sentence takeaway; text equivalents for major findings. Color is not the sole carrier of status; do not rely on red/green alone. Format probabilities consistently to one decimal percentage point. Use restrained color, legible tables, meaningful focus/order, and non-truncated axes unless a clearly explained scale requires otherwise. Do not claim WCAG certification without an audit.

## Reproducibility and Versioning

Visible metadata: dashboard version, project name, model reference, source-data coverage, unit of analysis, primary model, and final A6 commit `78f89c6` (or resolved full hash). After implementation, document environment/run command, provenance of displayed tables, and distinction between immutable A6 artifacts and A7 transformations. Do not expose local paths. Pin app dependencies and contracts in later stages.

## Future Map Integration

Reserve a future geographic component keyed by CBSA code/name, with identified/licensed geometry source and vintage, year role, sector, alignment, gap status, risk score, and coverage. Future modes may show alignment, predicted risk, sector filtering, MSA highlighting, and popup details. A full map is deferred until post-A7 visualization/presentation work; no geometry or map code is in scope now.

## A7.1 Source Inventory

| Source | Existing artifact / role | Safe use and caveat |
| --- | --- | --- |
| Final holdout predictions | `reports/tables/a6_final_holdout_predictions.csv`; 10,304 rows with CBSA, sector, predictor/target year, actual gap, logistic/HGB probabilities, sector title. | Retrospective final holdout only; not a general historical score panel or prospective live feed. Actual gap is a later realized target. |
| Final model performance | `reports/tables/a6_final_model_performance.csv`; development OOF and holdout benchmark/model metrics. | Fixed performance and overview summaries; preserve dataset/model labels. |
| Final calibration | `reports/tables/a6_final_holdout_calibration.csv`; risk bins and observed target prevalence. | Holdout diagnostic only; not calibration parameters or a recalibration table. |
| Final by year | `reports/tables/a6_final_holdout_by_year.csv`; predictor/target years, model, N, prevalence, AP, ROC-AUC, Brier. | Descriptive diagnostics; label year roles. |
| Final by sector | `reports/tables/a6_final_holdout_by_sector.csv`; event counts, prevalence, model AP/ROC-AUC, sufficiency flag. | Descriptive only; metrics suppressed below 30 positives or with no negative class. |
| Final by MSA size | `reports/tables/a6_final_holdout_by_msa_size.csv`; group counts, prevalence and model scores. | Descriptive holdout subgroup view; training-derived cutpoints in `a6_final_msa_size_cutpoints.csv`. |
| Robustness scorecard | `reports/tables/a6_robustness_scorecard.csv` and related `a6_*robustness*.csv`. | Development OOF sensitivity evidence only; never mix with holdout or present as current probability. |
| Selection/coverage | `a6_sample_selection_audit.csv`, `a6_gap_complete_case_selection.csv`, `a6_msa_coverage_audit.csv`, `a6_msa_coverage_summary.csv`, `a6_final_sample_audit.csv`. | Retain each artifact's grain and denominator. |
| Analytical panel | Read-only `database/assignment4_production.sqlite`, view `v_analytics_msa_industry_year`; geography/industry keys, BDS startup measures/lags, QCEW employment/growth, ACS controls, CBP measures, suppression/match/coverage flags. | Historical descriptive inputs. View has no fitted expected rate, residual/alignment, or A6 gap label; those require traced A7.2 integration. UI never writes to canonical DB. |
| Limitations | `docs/ASSIGNMENT6_LIMITATIONS.md`, `reports/assignment6_final_analytics_engine.md`. | Source for warnings and method text; preserve selection, construct, calibration, subgroup, and temporal caveats. |

The final A6 artifacts exist. The repository has a dashboard package initializer only (`dashboard/__init__.py`), with no Streamlit app, pages, production charts, or A7 data layer at A7.1 start.

## Success Criteria for A7

- **Functional:** local app loads; all five pages render; scoped filters update intended views; CSV export matches visible filters and fields.
- **Analytical:** displayed metrics reconcile exactly to frozen A6 artifacts; year roles and denominators are visible; no target leakage, silent imputation, or inconsistent recomputation.
- **UX:** users can find eligible higher-risk pairs, explain the gap, compare observed and expected activity, and locate limitations.
- **Reproducibility:** documented command works in pinned environment; source lineage and data-layer build repeat without mutating canonical inputs.
- **Deployment:** identified container/cloud target runs reproducibly, with configuration and data access documented; no enterprise platform requirement.
