from __future__ import annotations

import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.dashboard.charts import (
    build_calibration_chart, build_lift_chart, build_model_comparison_chart,
    build_top_risk_table, format_lift, format_probability, format_score,
)
from regional_entrepreneurship_intelligence.dashboard.overview_data import (
    HOLDOUT_TABLE_LABEL, TOP_N_OPTIONS, OverviewDataError, get_metric,
    load_overview_data, validate_overview_data,
)


class DashboardOverviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_overview_data()

    def test_validated_a72_inputs_and_locked_model_hierarchy(self):
        self.assertIs(validate_overview_data(self.data), self.data)
        self.assertEqual(self.data["metadata"]["primary_model"], "logistic")
        self.assertEqual(self.data["metadata"]["sensitivity_model"], "hist_gradient_boosting")
        holdout = self.data["predictions"].query("development_or_holdout == 'final_holdout'")
        expected_n = self.data["model_summary"].query(
            "dataset_split == 'final_holdout' and model == 'logistic' and metric == 'AP'"
        )["sample_n"].iloc[0]
        self.assertEqual(len(holdout), int(expected_n))

    def test_invalid_model_hierarchy_and_missing_metric_fail(self):
        bad = dict(self.data)
        bad["metadata"] = {**self.data["metadata"], "primary_model": "hist_gradient_boosting"}
        with self.assertRaisesRegex(OverviewDataError, "primary_model"):
            validate_overview_data(bad)
        with self.assertRaises(OverviewDataError):
            get_metric(self.data["model_summary"], "not_a_split", "logistic", "AP")

    def test_top_n_table_is_ranked_and_explicitly_retrospective(self):
        self.assertEqual(TOP_N_OPTIONS, (10, 25, 50))
        table = build_top_risk_table(self.data["predictions"], labels=self.data["labels"])
        self.assertEqual(len(table), 10)
        self.assertTrue(table["Predicted probability of gap"].is_monotonic_decreasing)
        self.assertIn("retrospective", HOLDOUT_TABLE_LABEL.lower())
        self.assertIn("Observed target-year gap (retrospective)", table.columns)
        expected_labels = set(self.data["labels"]["gap_status"].values())
        self.assertTrue(set(table["Observed target-year gap (retrospective)"].unique()).issubset(expected_labels))
        self.assertIn("Entrepreneurial gap under the A6 p20 definition", expected_labels)
        with self.assertRaises(ValueError):
            build_top_risk_table(self.data["predictions"], top_n=20)

    def test_plotly_figures_are_source_driven_and_brier_direction_is_clear(self):
        comparison = build_model_comparison_chart(self.data["model_summary"])
        lift = build_lift_chart(self.data["model_summary"])
        calibration = build_calibration_chart(self.data["calibration"])
        self.assertEqual(len(comparison.data), 4)
        self.assertEqual(comparison.layout.yaxis2.title.text, "Brier score (lower is better)")
        self.assertEqual(len(lift.data[0].y), 3)
        self.assertEqual(len(calibration.data), 2)
        self.assertEqual(float(lift.data[0].y[0]), get_metric(
            self.data["model_summary"], "final_holdout", "logistic", "top10_lift"
        ))

    def test_display_format_helpers(self):
        self.assertEqual(format_probability(0.25), "25.0%")
        self.assertEqual(format_score(0.404225), "0.404")
        self.assertEqual(format_lift(1.985488), "1.99×")

    def test_page_is_independent_of_explorer_filters_and_risk_bands(self):
        page = Path(__file__).parents[1] / "src/regional_entrepreneurship_intelligence/dashboard/pages/overview.py"
        source = page.read_text(encoding="utf-8")
        self.assertNotIn("filter_state", source)
        self.assertNotIn("risk_category", source)
        self.assertIn("load_overview_data()", source)


if __name__ == "__main__":
    unittest.main()
