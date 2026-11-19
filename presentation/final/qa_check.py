"""Reproducible static checks for the final HTML presentation."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent


class DeckParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.slides: list[dict[str, object]] = []
        self.assets: list[str] = []
        self._current: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        if tag == "section" and "slide" in classes:
            self._current = {
                "backup": "backup" in classes,
                "title": values.get("data-title"),
                "time": values.get("data-time"),
                "notes": 0,
                "cues": 0,
            }
            self.slides.append(self._current)
        if self._current and "full-notes" in classes:
            self._current["notes"] = int(self._current["notes"]) + 1
        if self._current and tag == "ul" and "cues" in classes:
            self._current["cues"] = int(self._current["cues"]) + 1
        if tag in {"img", "script", "link"}:
            asset = values.get("src") or values.get("href")
            if asset and not asset.startswith(("http://", "https://", "#")):
                self.assets.append(asset)

    def handle_endtag(self, tag: str) -> None:
        if tag == "section":
            self._current = None


def main() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    script = (ROOT / "SPEAKER_SCRIPT.md").read_text(encoding="utf-8")
    parser = DeckParser()
    parser.feed(html)

    main_slides = [slide for slide in parser.slides if not slide["backup"]]
    backup_slides = [slide for slide in parser.slides if slide["backup"]]
    assert len(main_slides) == 17, f"Expected 17 main slides, found {len(main_slides)}"
    assert len(backup_slides) == 7, f"Expected 7 backup slides, found {len(backup_slides)}"
    assert all(slide["title"] for slide in parser.slides), "Every slide needs a title"
    assert all(slide["time"] for slide in main_slides), "Every main slide needs timing metadata"
    assert all(slide["notes"] == 1 for slide in main_slides), "Every main slide needs full notes"
    assert all(slide["cues"] == 1 for slide in main_slides), "Every main slide needs cues"
    assert sum(int(slide["time"]) for slide in main_slides) == 680, "Timing must total 11:20"

    for asset in parser.assets:
        assert (ROOT / asset).is_file(), f"Missing local asset: {asset}"

    canonical = [
        "63,577", "381", "19", "0.404", "23.3%", "0.692", "0.164", "1.99×",
        "0.424", "+0.020", "+0.006 to +0.034", "0.325", "+0.079", "17 / 17",
        "1,031", "476", "46.2%", "19.9%", "1.17", "12,091", "10,304",
        "85.2%", "14.8%", "17.3%", "10.7%", "6.6%", "19.1%",
    ]
    for value in canonical:
        assert value in html, f"Missing canonical display value: {value}"

    combined = f"{html}\n{script}".lower()
    prohibited = [
        r"\bhigh accuracy\b", r"\bpredicts with 40% accuracy\b", r"\bproves\b",
        r"\beconomic growth leads to entrepreneurship\b", r"\becosystem failure\b",
        r"\bfailed market\b", r"\bmodel knows\b", r"\bartificial intelligence discovered\b",
        r"\bcurrent national prediction\b", r"\b404 means 40\.4% correct\b",
    ]
    for pattern in prohibited:
        assert not re.search(pattern, combined), f"Prohibited claim found: {pattern}"

    print("Presentation QA passed")
    print(f"Main slides: {len(main_slides)}")
    print(f"Backup slides: {len(backup_slides)}")
    print("Planned time: 680 seconds (11:20)")
    print(f"Local assets checked: {len(parser.assets)}")


if __name__ == "__main__":
    main()
