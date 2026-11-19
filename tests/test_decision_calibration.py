from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from regional_entrepreneurship_intelligence.models.decision_calibration import (
    evaluate_selection,
    evaluate_threshold,
    evaluate_top_fraction,
    rank_top_fraction,
)


class DecisionCalibrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pd.DataFrame(
            {
                "cbsa_code": ["b", "a", "c", "d", "e", "f"],
                "sector_code": ["11"] * 6,
                "predictor_year": [2018] * 6,
                "target_year": [2021] * 6,
                "actual_gap": [1, 0, 1, 0, 1, 0],
                "predicted_probability_logistic": [0.9, 0.9, 0.8, 0.7, 0.6, 0.1],
            }
        )

    def test_top_fraction_uses_ceiling_count_and_correct_metrics(self):
        _, metrics = evaluate_top_fraction(self.frame, 0.50)
        self.assertEqual(metrics["flagged_n"], 3)
        self.assertEqual(metrics["true_positive_n"], 2)
        self.assertEqual(metrics["false_positive_n"], 1)
        self.assertAlmostEqual(metrics["precision"], 2 / 3)
        self.assertAlmostEqual(metrics["recall"], 2 / 3)
        self.assertAlmostEqual(metrics["false_positives_per_true_positive"], 0.5)

    def test_ties_use_keys_deterministically_and_exactly(self):
        ranked = rank_top_fraction(self.frame, 1 / 6)
        self.assertEqual(int(ranked.selected.sum()), 1)
        self.assertEqual(ranked.loc[ranked.selected, "cbsa_code"].item(), "a")
        reranked = rank_top_fraction(self.frame.sample(frac=1, random_state=44), 1 / 6)
        self.assertEqual(reranked.loc[reranked.selected, "cbsa_code"].item(), "a")

    def test_threshold_is_inclusive_and_reports_burden(self):
        metrics = evaluate_threshold(self.frame, 0.8)
        self.assertEqual(metrics["flagged_n"], 3)
        self.assertEqual(metrics["true_positive_n"], 2)
        self.assertEqual(metrics["false_positive_n"], 1)
        self.assertAlmostEqual(metrics["false_positive_share"], 1 / 3)

    def test_inputs_are_not_mutated(self):
        before = self.frame.copy(deep=True)
        evaluate_top_fraction(self.frame, 0.25)
        evaluate_threshold(self.frame, 0.5)
        pd.testing.assert_frame_equal(self.frame, before)

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "fraction"):
            rank_top_fraction(self.frame, 0)
        with self.assertRaisesRegex(ValueError, "unique"):
            rank_top_fraction(pd.concat([self.frame, self.frame.iloc[[0]]]), 0.5)
        with self.assertRaisesRegex(ValueError, "boolean"):
            evaluate_selection(self.frame, [1, 0, 1, 0, 0, 0], rule="bad")

    def test_frozen_holdout_reproduces_committed_operating_counts(self):
        root = Path(__file__).resolve().parents[1]
        holdout = pd.read_csv(
            root / "reports" / "tables" / "a6_final_holdout_predictions.csv",
            dtype={"cbsa_code": str, "sector_code": str},
        )
        _, top_ten = evaluate_top_fraction(holdout, 0.10)
        threshold = evaluate_threshold(holdout, 0.1883479994798214)
        self.assertEqual(
            (top_ten["flagged_n"], top_ten["true_positive_n"], top_ten["false_positive_n"]),
            (1031, 476, 555),
        )
        self.assertEqual(
            (threshold["flagged_n"], threshold["true_positive_n"], threshold["false_positive_n"]),
            (5173, 1696, 3477),
        )


if __name__ == "__main__":
    unittest.main()
