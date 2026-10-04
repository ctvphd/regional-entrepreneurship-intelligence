from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.models.gap import (
    apply_gap_threshold,
    calculate_gap_thresholds,
    compare_gap_definitions,
    construct_gap_labels,
    construct_t_plus_3_pairs,
    summarize_gap_prevalence,
    validate_gap_target,
)


class GapTargetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.training_residuals = pd.Series(np.arange(-10, 90, dtype=float))
        self.thresholds = calculate_gap_thresholds(self.training_residuals)

    def test_thresholds_come_only_from_training_residuals(self) -> None:
        base = calculate_gap_thresholds(self.training_residuals)
        validation = pd.Series([-10000.0, 10000.0])
        apply_gap_threshold(validation, base["primary_threshold"])
        self.assertEqual(base, calculate_gap_thresholds(self.training_residuals))
        self.assertAlmostEqual(base["primary_threshold"], self.training_residuals.quantile(.20))
        self.assertEqual(base["primary_threshold"], base["residual_p20"])

    def test_robustness_thresholds_use_same_training_residual_sample(self) -> None:
        thresholds = self.thresholds
        self.assertAlmostEqual(thresholds["residual_p10"], self.training_residuals.quantile(.10))
        self.assertAlmostEqual(thresholds["residual_p25"], self.training_residuals.quantile(.25))
        self.assertAlmostEqual(
            thresholds["residual_minus_1sd"],
            self.training_residuals.mean() - self.training_residuals.std(ddof=1),
        )

    def test_residual_rule_is_inclusive_and_margin_is_signed_distance(self) -> None:
        rows = pd.DataFrame({"alignment_residual": [-1.0, 0.0, 1.0, 2.0]})
        cutoffs = {"p10": 0, "p20": 1, "p25": 2, "mean_minus_1sd": -1}
        before = rows.copy(deep=True)
        labels = construct_gap_labels(rows, cutoffs)
        self.assertEqual(labels.gap_p20.tolist(), [1, 1, 1, 0])
        self.assertEqual(labels.gap_p10.tolist(), [1, 1, 0, 0])
        self.assertEqual(labels.gap_p25.tolist(), [1, 1, 1, 1])
        self.assertEqual(labels.gap_minus_1sd.tolist(), [1, 0, 0, 0])
        self.assertEqual(labels.gap_margin.tolist(), [-2.0, -1.0, 0.0, 1.0])
        pd.testing.assert_frame_equal(rows, before)

    def test_exact_t3_pairing_requires_same_msa_sector_and_calendar_year(self) -> None:
        keys = pd.DataFrame(
            [
                ("001", "11", 2015, 8.0), ("001", "11", 2018, 9.0),
                ("001", "11", 2019, 10.0), ("001", "21", 2018, 4.0),
                ("002", "11", 2018, 5.0), ("003", "11", 2015, 2.0),
                ("003", "11", 2019, 1.0),
            ],
            columns=["cbsa_code", "sector_code", "year", "startup_rate"],
        )
        pairs = construct_t_plus_3_pairs(
            keys, predictor_start_year=2015, predictor_end_year=2015
        )
        self.assertEqual(
            pairs[["cbsa_code", "sector_code", "predictor_year", "target_year"]].values.tolist(),
            [["001", "11", 2015, 2018]],
        )
        self.assertNotIn("startup_rate", pairs.columns)

    def test_prevalence_preserves_natural_class_rate_and_sensitivities(self) -> None:
        rows = pd.DataFrame({
            "fold": ["f1"] * 5,
            "gap_p10": [1, 0, 0, 0, 0],
            "gap_p20": [1, 1, 0, 0, 0],
            "gap_p25": [1, 1, 1, 0, 0],
            "gap_minus_1sd": [1, 0, 0, 0, 0],
        })
        summary = summarize_gap_prevalence(rows, group_columns=("fold",))
        self.assertEqual(summary.loc[0, "eligible_n"], 5)
        self.assertEqual(summary.loc[0, "gap_n"], 2)
        self.assertEqual(summary.loc[0, "gap_prevalence"], .4)
        robust = compare_gap_definitions(rows, group_columns=("fold",))
        self.assertEqual(set(robust.threshold_definition), {"p10", "p20", "p25", "mean_minus_1sd"})
        self.assertEqual(int(robust.loc[robust.threshold_definition.eq("p20"), "gap_n"].iloc[0]), 2)

    def test_target_validator_rejects_holdout_and_noncalendar_pairs(self) -> None:
        valid = pd.DataFrame({
            "fold": ["fold_1"], "split_role": ["validation"], "cbsa_code": ["001"],
            "sector_code": ["11"], "predictor_year": [2014], "target_year": [2017], "gap_p20": [1],
        })
        validate_gap_target(valid)
        holdout = valid.assign(predictor_year=2018, target_year=2021)
        with self.assertRaisesRegex(ValueError, "holdout"):
            validate_gap_target(holdout)
        noncalendar = valid.assign(target_year=2018)
        with self.assertRaisesRegex(ValueError, "exact calendar"):
            validate_gap_target(noncalendar)

    def test_gap_target_requires_binary_primary_label(self) -> None:
        frame = pd.DataFrame({
            "cbsa_code": ["001"], "sector_code": ["11"], "predictor_year": [2014],
            "target_year": [2017], "gap_p20": [2],
        })
        with self.assertRaisesRegex(ValueError, "binary"):
            validate_gap_target(frame)


if __name__ == "__main__":
    unittest.main()
