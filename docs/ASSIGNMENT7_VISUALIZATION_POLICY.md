# Assignment 7 Visualization Policy

## Interactive Dashboard

Use Plotly for interactive bar/line charts, risk deciles, lift, rankings, fixed model comparisons, and trend exploration. Interactivity must not imply model refitting or change fixed A6 denominators. Annotate predictor/target years and populations. Every chart has a descriptive title, subtitle, axes/units, and one-sentence takeaway.

## Static Research Artifacts

Retain existing Matplotlib A5/A6 figures as reproducibility and research-archive artifacts. Do not replace or delete them for the dashboard. Seaborn/Matplotlib publication redesign is deferred until post-A7 visual refinement.

## Design Principles

- Professional, high-contrast product interface with a dark-first default and a coherent user-selectable light theme.
- Restrained color; status is never encoded by color alone and not red/green only.
- Clear units, consistent one-decimal probability percentages, legible categories, and text equivalents.
- No misleading axis truncation; if a nonzero baseline is analytically necessary, mark and explain it.
- No decorative 3D charts. Avoid clutter and long paragraphs beneath every visual.
- Risk, coverage, and uncertainty annotations stay close to the plotted result.

## A7.8 Shared Visual System

- Plotly figures use `dashboard.visual_style.apply_dashboard_style` for typography, white surfaces, hover labels, axes, and responsive sizing. Page rendering uses `PLOTLY_CONFIG` with no scroll zoom or persistent toolbar.
- Semantic palette: observed/logistic primary `#176B5B`; expected `#5777A8`; HGB sensitivity/final temporal holdout `#C56A3B`; reference/development/insufficient sample `#64736E`; thin coverage `#A66E28`; gap `#7A3E8E`. Expected/HGB/different splits also use line/marker/pattern or explicit text cues; meaning is not color-only.
- Display precision is shared: probabilities one decimal percent; source startup rate two decimals; employment growth one decimal percent; alignment two decimals in percentage points; scores three decimals; lift two decimals with `×`; counts comma-separated; years integer.
- Canonical evaluation labels are `Development OOF` and `Final temporal holdout`. Logistic remains the primary model; HGB is a patterned sensitivity series.
- Metric and construct help text is maintained in `dashboard.glossary.GLOSSARY`. Chart context, subtitles, and takeaways remain outside figures so the plot area stays uncluttered.

## A7.8B Product Presentation

- Page navigation uses short, task-oriented labels; each page opens with a practical question and concise explanation.
- Plain language leads. Exact scientific terms, metric names, split semantics, and methodological caveats remain in metric labels, tooltips, or technical expanders.
- KPI cards use native bordered Streamlit containers, a clear primary value, an exact technical label, and one short interpretation. Cards are reserved for key metrics and status summaries rather than every section.
- Typography uses the supported Streamlit system sans-serif stack. Theme radius and border settings provide restrained card shape without custom CSS or external fonts.
- Plotly uses Streamlit's active theme so plot background, text, grid, and hover surfaces adapt to dark or light mode. Semantic series colors remain reinforced with labels, markers, patterns, and line styles.
- Shared chart colors use teal `#347C6A` for observed activity and the logistic primary; blue `#5777A8` for expected activity; orange `#C56A3B` for HGB/final evaluation; purple `#9465A4` for observed gaps; gray `#7A8983` for references/development; and gold `#A66E28` for limited coverage.
- Gap wording describes a model-relative comparison, never a judgment about a place. Scores are historical evaluation values, not current forecasts or causal claims.
- Coverage uses plain display labels “Good comparison coverage” and “Limited data coverage”; canonical A5 values remain `comparison_eligible` and `thin` in technical context. Coverage is not confidence.
