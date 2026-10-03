"""Offline checks for national BDS study-window selection."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.etl.run_bds_production import _extract


class BDSProductionExtractTest(unittest.TestCase):
    def test_age_zero_extract_preserves_all_study_years_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.csv"
            destination = Path(directory) / "extract.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["year", "msa", "sector", "fagecoarse"])
                writer.writeheader()
                for year, age in ((2009, "a) 0"), (2010, "a) 0"),
                                  (2010, "b) 1 to 5"), (2023, "a) 0"),
                                  (2024, "a) 0")):
                    writer.writerow({"year": year, "msa": "10180", "sector": "23", "fagecoarse": age})
            total, selected = _extract(source, destination, age_zero_only=True)
            with destination.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual((total, selected), (5, 2))
            self.assertEqual([row["year"] for row in rows], ["2010", "2023"])


if __name__ == "__main__":
    unittest.main()
