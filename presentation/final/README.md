# Final HTML Presentation

This directory contains the standalone 17-slide classroom presentation for **Regional Entrepreneurship Intelligence**, plus seven Q&A backup slides.

## Run locally

From the repository root:

```powershell
uv run python -m http.server 8765 --directory presentation/final
```

Open `http://localhost:8765/`.

The presentation also works when `index.html` is opened directly. A local HTTP server is recommended for consistent browser behavior.

## Navigation

- `Right arrow`, `Page Down`, or `Space`: reveal the next item or advance
- `Left arrow` or `Page Up`: go back
- `Home` / `End`: first / last slide in the current group
- Click the right or left half of a slide: advance or go back
- `B`: enter or leave Q&A backup slides
- `Escape`: leave backup slides
- `F`: toggle fullscreen
- `P`: open presenter view

## Presenter mode

Press `P`, or open:

`http://localhost:8765/?presenter=1`

The presenter window includes the current slide, next-slide preview, full notes, concise cues, elapsed time, target time, and slide number. Audience and presenter windows synchronize through browser local storage.

## Print to PDF

Use the browser's print command and choose **Save as PDF**. Recommended settings:

- Layout: Landscape
- Margins: None
- Background graphics: On
- Scale: Default / 100%

Print CSS produces one 16:9 slide per page and excludes notes and controls. Backup slides are included after the 17-slide main deck.

## Live demo

Validated local route: `http://localhost:8772/explorer`

Start the dashboard from the repository root if needed:

```powershell
uv run python -m streamlit run streamlit_app.py --server.port 8772
```

No current working deployed Streamlit URL is documented in the repository. The live-demo button therefore opens the validated local route. Slide 16 includes an actual application screenshot as a fallback.

Selected case: **Pittsburgh, PA × Arts, Entertainment, and Recreation (NAICS 71)**.

Backup case: **Fort Collins-Loveland, CO × Transportation and Warehousing (NAICS 48-49)**.

## Data provenance

Presentation metrics come from frozen Assignment 6 and Assignment 7 artifacts. No models were retrained and no targets or predictions were changed. See [DATA_PROVENANCE.md](DATA_PROVENANCE.md) for slide-level mapping and [SPEAKER_SCRIPT.md](SPEAKER_SCRIPT.md) for the timed narrative.

## File map

- `index.html`: semantic slide content and presenter notes
- `styles.css`: 16:9 layout, visual system, responsive and print styles
- `app.js`: navigation, progressive reveals, presenter mode, timing, and fullscreen
- `assets/figures/`: copied frozen production figures used by the deck
- `assets/screenshots/`: actual current dashboard screenshot
- `DATA_PROVENANCE.md`: claim-to-artifact audit trail
- `SPEAKER_SCRIPT.md`: full script, cues, transitions, and timing
- `BUILD_REPORT.md`: QA and deployment status
