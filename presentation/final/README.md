# Final HTML Presentation

This directory contains the standalone 17-slide classroom presentation for **Regional Entrepreneurship Intelligence**, plus seven Q&A backup slides.

## Run locally

From the repository root:

```powershell
uv run python -m http.server 8765 --directory presentation/final
```

Open `http://localhost:8765/REI%20Presentation.html`.

The presentation also works when `REI Presentation.html` is opened directly. A local HTTP server is recommended for consistent browser behavior.

## Navigation

- `Right arrow`, `Page Down`, or `Space`: reveal the next item or advance
- `Left arrow` or `Page Up`: go back
- `Home` / `End`: first / last slide in the current group
- Click the right or left half of a slide: advance or go back
- `Q&A` button or `B`: enter or leave the seven technical Q&A backup slides
- `Escape`: leave backup slides
- `F`: toggle fullscreen
- `Notes` button or `P`: enter or leave presenter notes view

## Presenter mode

Press `P` or select **Notes**. Presenter view replaces the audience slide in the same tab and includes the current slide, next-slide preview, full notes, concise cues, elapsed time, target time, and slide number. Select **Exit notes** to return to the audience view.

Slides 1–17 are the timed classroom presentation. Slides B1–B7 are technical Q&A backups and are excluded from the planned speaking time.

## Print to PDF

Use the browser's print command and choose **Save as PDF**. Recommended settings:

- Layout: Landscape
- Margins: None
- Background graphics: On
- Scale: Default / 100%

Print CSS produces one 16:9 slide per page and excludes notes and controls. Backup slides are included after the 17-slide main deck.

## Live demo

Verified public dashboard: `https://regional-entrepreneurship-intelligence-sag3gkhdnpptv6hbxapp6yn.streamlit.app/`

Slide 16 opens the public Explorer directly:

`https://regional-entrepreneurship-intelligence-sag3gkhdnpptv6hbxapp6yn.streamlit.app/explorer`

Start the dashboard from the repository root if needed:

```powershell
uv run python -m streamlit run streamlit_app.py --server.port 8772
```

The public Overview and Explorer routes were verified on November 21, 2026. Their visible title, navigation, model roles, 2010–2023 period, AP 0.404, and top-decile lift 1.99× match the current committed dashboard. Slide 16 includes an actual application screenshot as a fallback.

Selected case: **Pittsburgh, PA × Arts, Entertainment, and Recreation (NAICS 71)**.

Backup case: **Fort Collins-Loveland, CO × Transportation and Warehousing (NAICS 48-49)**.

## Data provenance

Presentation metrics come from frozen Assignment 6 and Assignment 7 artifacts. No models were retrained and no targets or predictions were changed. See [DATA_PROVENANCE.md](DATA_PROVENANCE.md) for slide-level mapping and [SPEAKER_SCRIPT.md](SPEAKER_SCRIPT.md) for the timed narrative.

## File map

- `REI Presentation.html`: semantic slide content and presenter notes
- `styles.css`: 16:9 layout, visual system, responsive and print styles
- `app.js`: navigation, progressive reveals, presenter mode, timing, and fullscreen
- `assets/figures/`: copied frozen production figures used by the deck
- `assets/screenshots/`: actual current dashboard screenshot
- `DATA_PROVENANCE.md`: claim-to-artifact audit trail
- `SPEAKER_SCRIPT.md`: full script, cues, transitions, and timing
- `LANGUAGE_AUDIENCE_QA.md`: doctoral, economics, and local-government language review
- `BUILD_REPORT.md`: QA and deployment status
