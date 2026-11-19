from __future__ import annotations

import unittest

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from regional_entrepreneurship_intelligence.models.bootstrap import (
    _cluster_row_indices,
    _draw_cluster_rows,
    paired_cluster_bootstrap_ap,
)
from regional_entrepreneurship_intelligence.models.run_bootstrap_uncertainty import (
    _development_stability,
    _load_frozen_predictions,
)


PREDICTIONS = {"logistic": "p_logistic", "hgb": "p_hgb"}


class _DuplicateFirstCluster:
    def integers(self, low, high, size):
        return np.array([0, 0, 1])


class BootstrapUncertaintyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pd.DataFrame(
            {
                "msa": ["a", "a", "b", "b", "c", "c"],
                "label": [0, 1, 0, 1, 0, 1],
                "p_logistic": [0.1, 0.7, 0.3, 0.6, 0.2, 0.8],
                "p_hgb": [0.05, 0.8, 0.2, 0.7, 0.1, 0.9],
            }
        )

    def test_fixed_seed_is_deterministic_paired_and_non_mutating(self):
        before = self.frame.copy(deep=True)
        first = paired_cluster_bootstrap_ap(
            self.frame,
            cluster_column="msa",
            label_column="label",
            prediction_columns=PREDICTIONS,
            comparison=("hgb", "logistic"),
            replications=100,
            seed=754,
            return_replications=True,
        )
        second = paired_cluster_bootstrap_ap(
            self.frame,
            cluster_column="msa",
            label_column="label",
            prediction_columns=PREDICTIONS,
            comparison=("hgb", "logistic"),
            replications=100,
            seed=754,
            return_replications=True,
        )
        pd.testing.assert_frame_equal(first.summary, second.summary)
        pd.testing.assert_frame_equal(first.replications, second.replications)
        pd.testing.assert_frame_equal(self.frame, before)
        np.testing.assert_allclose(
            first.replications.hgb_minus_logistic,
            first.replications.hgb - first.replications.logistic,
        )

    def test_cluster_draw_duplicates_every_row_of_reselected_cluster(self):
        rows = _cluster_row_indices(self.frame, "msa")
        sampled = _draw_cluster_rows(rows, _DuplicateFirstCluster())
        self.assertEqual(sampled.tolist(), [0, 1, 0, 1, 2, 3])

    def test_one_class_replicates_are_counted_and_excluded(self):
        frame = pd.DataFrame(
            {
                "msa": ["zero", "zero", "one", "one"],
                "label": [0, 0, 1, 1],
                "p_logistic": [0.1, 0.2, 0.8, 0.9],
                "p_hgb": [0.05, 0.15, 0.85, 0.95],
            }
        )
        result = paired_cluster_bootstrap_ap(
            frame,
            cluster_column="msa",
            label_column="label",
            prediction_columns=PREDICTIONS,
            comparison=("hgb", "logistic"),
            replications=200,
            seed=754,
        )
        self.assertGreater(result.diagnostics["invalid_replications"], 0)
        self.assertEqual(
            result.diagnostics["valid_replications"] + result.diagnostics["invalid_replications"],
            200,
        )

    def test_observed_toy_ap_and_difference_match_known_calculation(self):
        result = paired_cluster_bootstrap_ap(
            self.frame,
            cluster_column="msa",
            label_column="label",
            prediction_columns=PREDICTIONS,
            comparison=("hgb", "logistic"),
            replications=20,
            seed=7,
        )
        summary = result.summary.set_index("estimand")
        expected_logistic = average_precision_score(self.frame.label, self.frame.p_logistic)
        expected_hgb = average_precision_score(self.frame.label, self.frame.p_hgb)
        self.assertAlmostEqual(summary.loc["logistic", "observed"], expected_logistic)
        self.assertAlmostEqual(summary.loc["hgb", "observed"], expected_hgb)
        self.assertAlmostEqual(
            summary.loc["hgb_minus_logistic", "observed"], expected_hgb - expected_logistic
        )

    def test_missing_columns_and_invalid_labels_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            paired_cluster_bootstrap_ap(
                self.frame.drop(columns="p_hgb"),
                cluster_column="msa",
                label_column="label",
                prediction_columns=PREDICTIONS,
                comparison=("hgb", "logistic"),
            )
        with self.assertRaisesRegex(ValueError, "both classes"):
            paired_cluster_bootstrap_ap(
                self.frame.assign(label=1),
                cluster_column="msa",
                label_column="label",
                prediction_columns=PREDICTIONS,
                comparison=("hgb", "logistic"),
            )

    def test_frozen_holdout_and_development_evidence_are_unchanged(self):
        frame = _load_frozen_predictions()
        self.assertEqual(len(frame), 10304)
        self.assertEqual(frame.cbsa_code.nunique(), 365)
        self.assertEqual(sorted(frame.target_year.unique().tolist()), [2021, 2022, 2023])
        self.assertAlmostEqual(
            average_precision_score(frame.actual_gap, frame.predicted_probability_logistic),
            0.40422477786600497,
        )
        self.assertAlmostEqual(
            average_precision_score(frame.actual_gap, frame.predicted_probability_hgb),
            0.42423839854017453,
        )
        stability = _development_stability()
        self.assertEqual(stability["hgb_fold_wins"], 2)
        self.assertFalse(stability["all_folds_positive"])


if __name__ == "__main__":
    unittest.main()
