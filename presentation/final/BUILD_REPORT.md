# Final Presentation Build Report

## Scope

- 17 timed main slides
- 7 manually accessible Q&A backup slides
- Planned speaking time: 11:20
- Static HTML/CSS/JavaScript; no external runtime dependencies
- No changes to model science, predictions, targets, or shared dashboard code

## Demo

The selected demonstration case is Pittsburgh, PA × Arts, Entertainment, and Recreation. The Explorer state was validated in the running application and captured as `assets/screenshots/pittsburgh-arts-explorer.png`.

The repository does not document a current public deployment. The deck therefore uses the validated local URL `http://localhost:8772/explorer` and visibly labels the deployed URL as unavailable. The screenshot is the fallback.

## Visual and interaction QA

Presentation-specific automation checks:

- main and backup slide counts
- required metadata and speaker-note presence
- local asset existence
- canonical numeric strings
- prohibited-language scan
- 16:9 responsive rendering at 1920×1080 and 1366×768
- slide content overflow checks
- browser-console error checks
- presenter-mode rendering
- print-style presence

Manual review covers information hierarchy, direct labels, screenshot authenticity, claims, and the distinction between predictive screening and causal interpretation.

Browser QA passed at 1920×1080 and 1366×768 for all 17 main slides: no slide-level or direct-child overflow, no console warnings/errors, and successful presenter/backup rendering.

## Test results

- `presentation/final/qa_check.py`: passed; 17 main slides, 7 backups, 11:20 planned time, 5 local assets checked.
- `python -m unittest tests.test_reviewer_reproducibility`: 3 tests passed in 22.053 seconds.
- The full `unittest discover` run was attempted but stalled after early Streamlit tests with no failure output or further progress for more than ten minutes; it was stopped. This static presentation change does not modify shared Python code.

## Scientific boundaries

- AP is described as ranking performance, never accuracy.
- The gap is described as model-relative.
- The holdout scores are retrospective evaluations, not live forecasts.
- Coverage is reported alongside performance.
- High scores prioritize investigation and do not prescribe funding or intervention.
