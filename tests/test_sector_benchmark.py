from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from regional_entrepreneurship_intelligence.models.bootstrap import paired_cluster_bootstrap_ap
from regional_entrepreneurship_intelligence.models.sector_benchmark import (
    benchmark_performance,
    fit_sector_prevalence,
    score_sector_prevalence,
    within_sector_logistic_performance,
)


class SectorBenchmarkTest(unittest.TestCase):
    def setUp(self) -> None:
        self.development = pd.DataFrame(
            {
                "sector_code": ["11", "11", "11", "11", "21", "21", "21", "21"],
                "actual_gap": [0, 0, 1, 1, 0, 1, 1, 1],
            }
        )
        self.holdout = pd.DataFrame(
            {
                "cbsa_code": ["a", "a", "b", "b"],
                "sector_code": ["11", "21", "11", "21"],
                "actual_gap": [1, 0, 0, 1],
                "predicted_probability_logistic": [0.8, 0.2, 0.3, 0.7],
                "predicted_probability_hgb": [0.9, 0.1, 0.2, 0.8],
            }
        )

    def test_training_only_rates_and_deterministic_tied_scores_do_not_mutate_inputs(self):
        development_before = self.development.copy(deep=True)
        holdout_before = self.holdout.copy(deep=True)
        rates = fit_sector_prevalence(self.development)
        scored = score_sector_prevalence(self.holdout, rates)
        self.assertEqual(rates.set_index("sector_code").development_gap_prevalence.to_dict(), {"11": 0.5, "21": 0.75})
        self.assertEqual(scored.sector_only_probability.tolist(), [0.5, 0.75, 0.5, 0.75])
        self.assertEqual(scored.groupby("sector_code").sector_only_probability.nunique().max(), 1)
        pd.testing.assert_frame_equal(self.development, development_before)
        pd.testing.assert_frame_equal(self.holdout, holdout_before)

    def test_holdout_labels_cannot_change_fitted_sector_scores(self):
        rates = fit_sector_prevalence(self.development)
        first = score_sector_prevalence(self.holdout, rates).sector_only_probability
        second = score_sector_prevalence(
            self.holdout.assign(actual_gap=1 - self.holdout.actual_gap), rates
        ).sector_only_probability
        pd.testing.assert_series_equal(first, second)

    def test_unseen_sector_fails_closed_or_uses_explicit_fallback(self):
        rates = fit_sector_prevalence(self.development)
        unseen = self.holdout.assign(sector_code=["11", "21", "99", "21"])
        with self.assertRaisesRegex(ValueError, "unseen"):
            score_sector_prevalence(unseen, rates)
        scored = score_sector_prevalence(unseen, rates, unseen_fallback=0.6)
        self.assertEqual(float(scored.loc[2, "sector_only_probability"]), 0.6)

    def test_toy_performance_and_within_sector_suppression(self):
        rates = fit_sector_prevalence(self.development)
        scored = score_sector_prevalence(self.holdout, rates)
        metrics = benchmark_performance(scored.actual_gap, scored.sector_only_probability)
        self.assertEqual(metrics["n"], 4)
        self.assertTrue(0 <= metrics["AP"] <= 1)
        sectors = within_sector_logistic_performance(scored, minimum_positives=1)
        self.assertTrue(sectors.eligible.all())
        suppressed = within_sector_logistic_performance(scored, minimum_positives=2)
        self.assertFalse(suppressed.eligible.any())

    def test_sector_score_integrates_with_paired_cluster_bootstrap(self):
        rates = fit_sector_prevalence(self.development)
        scored = score_sector_prevalence(self.holdout, rates)
        result = paired_cluster_bootstrap_ap(
            scored,
            cluster_column="cbsa_code",
            label_column="actual_gap",
            prediction_columns={
                "sector": "sector_only_probability",
                "logistic": "predicted_probability_logistic",
            },
            comparison=("logistic", "sector"),
            replications=100,
            seed=755,
            return_replications=True,
        )
        self.assertIn("logistic_minus_sector", set(result.summary.estimand))
        self.assertEqual(
            result.diagnostics["valid_replications"] + result.diagnostics["invalid_replications"],
            100,
        )

    def test_missing_fields_and_nonbinary_labels_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            fit_sector_prevalence(self.development.drop(columns="sector_code"))
        with self.assertRaisesRegex(ValueError, "binary"):
            fit_sector_prevalence(self.development.assign(actual_gap=2))

    def test_frozen_artifacts_cover_all_holdout_sectors_without_leakage(self):
        root = Path(__file__).resolve().parents[1]
        development = pd.read_csv(
            root / "reports" / "tables" / "a6_baseline_oof_predictions.csv",
            dtype={"sector_code": str},
        )
        holdout = pd.read_csv(
            root / "reports" / "tables" / "a6_final_holdout_predictions.csv",
            dtype={"sector_code": str},
        )
        rates = fit_sector_prevalence(development)
        scored = score_sector_prevalence(holdout, rates)
        self.assertEqual(len(rates), 19)
        self.assertFalse(scored.sector_only_probability.isna().any())
        self.assertAlmostEqual(
            benchmark_performance(scored.actual_gap, scored.sector_only_probability)["AP"],
            0.3252357300495576,
        )


if __name__ == "__main__":
    unittest.main()
