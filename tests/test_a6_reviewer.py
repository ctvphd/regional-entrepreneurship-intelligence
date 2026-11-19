from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from regional_entrepreneurship_intelligence.models.features import validate_feature_timing
from regional_entrepreneurship_intelligence.models.reviewer import REVIEWER_WARNING
from regional_entrepreneurship_intelligence.models.run_assignment6 import run_assignment6


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ARTIFACTS = (
    ROOT / "reports" / "tables" / "a6_final_model_performance.csv",
    ROOT / "reports" / "tables" / "a6_final_holdout_predictions.csv",
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Assignment6ReviewerRunTest(unittest.TestCase):
    def test_explicit_reviewer_source_runs_t3_pipeline_with_isolated_outputs(self):
        before = {path: _hash(path) for path in PRODUCTION_ARTIFACTS}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "review" / "reviewer.sqlite"
            output = root / "review" / "assignment6"
            sources = root / "review" / "sources"
            result = run_assignment6(
                source="reviewer",
                reviewer_database=database,
                reviewer_output=output,
                reviewer_sources=sources,
            )
            self.assertEqual(result["warning"], REVIEWER_WARNING)
            self.assertEqual(result["fixture_years"], [2017, 2023])
            self.assertTrue(result["feature_registry_validated"])
            self.assertTrue(result["exact_horizon_validated"])
            self.assertGreater(result["development_rows"], 0)
            self.assertGreater(result["holdout_rows"], 0)
            self.assertEqual(result["development_classes"], [0, 1])

            design = json.loads((output / "temporal_design.json").read_text(encoding="utf-8"))
            self.assertEqual(design["development_predictor_years"], [2018, 2019])
            self.assertEqual(design["holdout_predictor_years"], [2020])
            self.assertEqual(design["horizon"], 3)
            predictions = pd.read_csv(output / "reviewer_predictions.csv")
            self.assertTrue(predictions.target_year.eq(predictions.predictor_year + 3).all())
            self.assertTrue({"gap_p20", "synthetic_gap_probability"}.issubset(predictions.columns))
            self.assertFalse((root / "reports" / "tables").exists())

        self.assertEqual(before, {path: _hash(path) for path in PRODUCTION_ARTIFACTS})

    def test_reviewer_mode_is_explicit_and_future_features_remain_prohibited(self):
        with self.assertRaisesRegex(ValueError, "Reviewer paths require"):
            run_assignment6(source="production", reviewer_output=Path("unused"))
        with self.assertRaisesRegex(ValueError, "Future outcome"):
            validate_feature_timing(["startup_rate", "gap_status_t_plus_3"])
        with self.assertRaisesRegex(ValueError, "production database"):
            run_assignment6(
                source="reviewer",
                reviewer_database=ROOT / "database" / "assignment4_production.sqlite",
                reviewer_output=ROOT / "database" / "reviewer-output",
            )


if __name__ == "__main__":
    unittest.main()
