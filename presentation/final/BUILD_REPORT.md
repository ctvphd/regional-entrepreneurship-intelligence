# Final Presentation Build Report

## Scope

- 17 timed main slides
- 7 manually accessible Q&A backup slides
- Planned speaking time: 11:20
- Static HTML/CSS/JavaScript; no external runtime dependencies
- No changes to model science, predictions, targets, or shared dashboard code

## Demo

The selected demonstration case is Pittsburgh, PA × Arts, Entertainment, and Recreation. The Explorer state was validated in the running application and captured as `assets/screenshots/pittsburgh-arts-explorer.png`.

The Slide 16 link uses the verified public Explorer route at `https://regional-entrepreneurship-intelligence-sag3gkhdnpptv6hbxapp6yn.streamlit.app/explorer`. The public Overview and Explorer loaded successfully on November 21, 2026, with the expected project title, routes, study period, model roles, AP 0.404, and top-decile lift 1.99×. The screenshot remains the fallback.

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

Browser QA passed at 1920×1080 and 1366×768 for all 17 main slides: no slide-level or direct-child overflow, no console warnings/errors, synchronized presenter notes, seven reachable backup slides, and an active print-media rule.

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

## Mixed-audience language pass

The final language-steadying pass applies a consistent order across the main deck: plain-language meaning, technical term, then statistic. Slides 6–15 received the most visible revisions; model names, confidence intervals, validation years, and canonical metrics remain unchanged. Slides 10–12 now use an explicit three-question transition: useful ranking, complex-model replacement, and value beyond industry identity.

Audience review is documented in `LANGUAGE_AUDIENCE_QA.md`. Average scores are 4.94/5 for a doctoral professor, 5.00/5 for an economist, and 4.76/5 for a local-government official; the lowest individual score is 4/5.

The revised script contains 1,174 spoken words. At a deliberate 110–120 words per minute, the words occupy approximately 9:47–10:40; planned pauses, slide transitions, and the dashboard demonstration retain the existing 11:20 delivery target without requiring faster speech.
