from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from regional_entrepreneurship_intelligence.models.drift_coverage import (
    classify_eligibility,
    exclusion_reason_table,
    standardized_mean_difference,
    standardized_prevalence,
)


class HoldoutDriftCoverageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reference = pd.DataFrame(
            {"sector": ["a", "a", "b", "b"], "actual_gap": [0, 1, 0, 0]}
        )
        self.comparison = pd.DataFrame(
            {"sector": ["a", "a", "b", "b"], "actual_gap": [1, 1, 0, 1]}
        )

    def test_composition_standardization_uses_reference_weights(self):
        result = standardized_prevalence(
            self.reference, self.comparison, strata=("sector",)
        )
        self.assertAlmostEqual(result["standardized_prevalence"], 0.75)
        self.assertEqual(result["strata_n"], 2)

    def test_eligibility_and_overlapping_exclusion_reasons(self):
        candidates = pd.DataFrame(
            {"target_x": [1.0, None, None], "predictor_x": [1.0, 1.0, None]}
        )
        classified = classify_eligibility(
            candidates,
            target_required=("target_x",),
            predictor_required=("predictor_x",),
        )
        self.assertEqual(classified.eligible.tolist(), [True, False, False])
        reasons = exclusion_reason_table(
            candidates,
            target_required=("target_x",),
            predictor_required=("predictor_x",),
        ).set_index("reason")
        self.assertEqual(reasons.loc["target benchmark inputs incomplete", "excluded_n"], 2)
        self.assertEqual(reasons.loc["both target and predictor inputs incomplete", "excluded_n"], 1)

    def test_helpers_do_not_mutate_inputs(self):
        before_reference = self.reference.copy(deep=True)
        before_comparison = self.comparison.copy(deep=True)
        standardized_prevalence(self.reference, self.comparison, strata=("sector",))
        pd.testing.assert_frame_equal(self.reference, before_reference)
        pd.testing.assert_frame_equal(self.comparison, before_comparison)

    def test_standardized_difference_uses_available_values(self):
        value = standardized_mean_difference(
            pd.Series([3.0, 4.0, 5.0]), pd.Series([1.0, 2.0, None])
        )
        self.assertGreater(value, 0)

    def test_frozen_sample_audit_has_exact_holdout_counts(self):
        root = Path(__file__).resolve().parents[1]
        audit = pd.read_csv(root / "reports" / "tables" / "a6_final_sample_audit.csv")
        holdout = audit[audit["sample"].eq("holdout")].iloc[0]
        self.assertEqual(
            (
                int(holdout.candidate_pairs),
                int(holdout.target_label_eligible_pairs),
                int(holdout.complete_case_eligible_pairs),
                int(holdout.excluded_pairs),
            ),
            (12091, 10924, 10304, 1787),
        )
        self.assertAlmostEqual(float(holdout.exclusion_share), 0.1477958812339757)


if __name__ == "__main__":
    unittest.main()
