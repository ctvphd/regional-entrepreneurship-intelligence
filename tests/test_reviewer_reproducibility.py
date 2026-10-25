from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.dashboard.loader import load_dataset
from regional_entrepreneurship_intelligence.database.connection import PROJECT_ROOT
from regional_entrepreneurship_intelligence.review.build_reviewer_fixture import build


class ReviewerReproducibilityTest(unittest.TestCase):
    def test_synthetic_end_to_end_build_is_repeatable_and_dashboard_loadable(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "data" / "review") as temporary:
            root = Path(temporary)
            database = root / "reviewer_fixture.sqlite"
            sources = root / "sources"
            first = build(database, sources)
            artifact = root / "dashboard" / "dashboard_msa_industry_year.parquet"
            first_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
            second = build(database, sources)
            second_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()

            self.assertEqual(first["label"], "Synthetic reviewer fixture")
            self.assertEqual(first["source_files"], 7)
            self.assertEqual(first["analytical_rows"], 27)
            self.assertEqual(first["msa_count"], 2)
            self.assertEqual(first["sector_count"], 2)
            self.assertEqual(first["year_min_max"], [2017, 2023])
            self.assertEqual(first["duplicate_keys"], 0)
            self.assertEqual(first["quality_check_count"], 4)
            self.assertEqual(first["foreign_key_violations"], 0)
            self.assertEqual(first["analytical_rows"], second["analytical_rows"])
            self.assertEqual(first["duplicate_keys"], second["duplicate_keys"])
            self.assertEqual(first_hash, second_hash)
            self.assertEqual(Path(first["database_path"]), database)

            panel = load_dataset("msa_industry_year", data_dir=artifact.parent)
            self.assertEqual(len(panel), 27)
            self.assertTrue({"cbsa_code", "sector_code", "year", "startup_rate"}.issubset(panel.columns))
            self.assertTrue(((panel.cbsa_code == "99901") & (panel.sector_code == "11") & (panel.year == 2020)).any())
            self.assertFalse(((panel.cbsa_code == "99902") & (panel.sector_code == "54") & (panel.year == 2019)).any())
            zero = panel.loc[(panel.cbsa_code == "99901") & (panel.sector_code == "11") & (panel.year == 2018), "startup_rate"]
            self.assertEqual(float(zero.iloc[0]), 0.0)
            missing_control = panel.loc[(panel.cbsa_code == "99902") & (panel.year == 2020), "acs_has_missing_controls"]
            self.assertTrue(missing_control.fillna(False).any())

    def test_generated_fixture_exposes_exact_three_year_pairs_and_prior_lags(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "data" / "review") as temporary:
            root = Path(temporary)
            build(root / "review.sqlite", root / "sources")
            import sqlite3

            connection = sqlite3.connect(root / "review.sqlite")
            try:
                years = {row[0] for row in connection.execute("SELECT year FROM analytics_msa_industry_year WHERE geography_id=(SELECT geography_id FROM ref_geography WHERE cbsa_code='99901') AND industry_id=(SELECT industry_id FROM ref_industry WHERE naics_code='11' AND naics_version='2022')")}
                self.assertIn(2020, years)
                self.assertIn(2023, years)
                predictor, target = 2020, 2023
                self.assertEqual(target, predictor + 3)
                row = connection.execute("SELECT startup_rate_lag1 FROM analytics_msa_industry_year WHERE year=2020 AND geography_id=(SELECT geography_id FROM ref_geography WHERE cbsa_code='99901') AND industry_id=(SELECT industry_id FROM ref_industry WHERE naics_code='11' AND naics_version='2022')").fetchone()
                prior = connection.execute("SELECT startup_rate FROM analytics_msa_industry_year WHERE year=2019 AND geography_id=(SELECT geography_id FROM ref_geography WHERE cbsa_code='99901') AND industry_id=(SELECT industry_id FROM ref_industry WHERE naics_code='11' AND naics_version='2022')").fetchone()
                self.assertEqual(row[0], prior[0])
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
