from __future__ import annotations

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from regional_entrepreneurship_intelligence.dashboard.charts import (
    build_calibration_chart,
    build_lift_comparison_chart,
    build_metric_comparison_chart,
    build_msa_size_performance_chart,
    build_performance_by_year_chart,
    build_performance_model_chart,
    build_pr_curve,
    build_reliability_chart,
    build_roc_curve,
    build_sector_performance_chart,
)
from regional_entrepreneurship_intelligence.dashboard.components import development_holdout_label
from regional_entrepreneurship_intelligence.dashboard.overview_data import get_metric
from regional_entrepreneurship_intelligence.dashboard.overview_data import load_overview_data
from regional_entrepreneurship_intelligence.dashboard.performance_data import (
    EXPECTED_HOLDOUT_PAIRS,
    PerformanceDataError,
    build_risk_concentration_table,
    build_sector_performance_table,
    load_performance_data,
    metric_value,
    validate_performance_data,
)


class DashboardPerformanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_performance_data()

    def test_fixed_metrics_ignore_explorer_state_and_model_hierarchy_is_locked(self):
        summary = self.data["model_summary"]
        fixed_ap = get_metric(summary, "final_holdout", "logistic", "AP")
        app = AppTest.from_string(
            "from regional_entrepreneurship_intelligence.dashboard.pages import performance\nperformance.render()",
            default_timeout=45,
        )
        app.session_state["selected_msa"] = "35620"
        app.session_state["selected_sectors"] = ["44-45"]
        app.session_state["selected_year"] = 2020
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(get_metric(summary, "final_holdout", "logistic", "AP"), fixed_ap)
        self.assertEqual(self.data["metadata"]["primary_model"], "logistic")
        self.assertEqual(self.data["metadata"]["sensitivity_model"], "hist_gradient_boosting")
        self.assertNotIn("random_forest", set(summary.model.astype(str)))
        self.assertTrue(any(item.label == "Average Precision" and item.value == "0.404" for item in app.metric))
        self.assertTrue(any("Random Forest is not shown" in item.value for item in app.caption))
        self.assertFalse(any(item.label in {"Metropolitan area", "NAICS sector"} for item in app.selectbox))
        self.assertGreaterEqual(len(app.get("plotly_chart")), 10)
        app.get_by_key("performance_curve_split").set_value("development_oof").run()
        app.get_by_key("performance_include_hgb").check().run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any(item.label == "Average Precision" and item.value == "0.404" for item in app.metric))

    def test_standard_split_labels_and_brier_direction_are_explicit(self):
        self.assertEqual(self.data["metadata"]["primary_model"], "logistic")
        page = Path(__file__).parents[1] / "src/regional_entrepreneurship_intelligence/dashboard/pages/performance.py"
        text = page.read_text(encoding="utf-8")
        self.assertEqual(development_holdout_label("development_oof"), "Development OOF")
        self.assertEqual(development_holdout_label("final_holdout"), "Final temporal holdout")
        self.assertIn("Brier probability error: lower is better", text)
        self.assertIn("Brier {brier_delta:+.3f}", text)

    def test_overview_and_performance_metrics_reconcile_to_the_same_artifact(self):
        overview = load_overview_data()
        for metric in ("AP", "prevalence", "ROC_AUC", "Brier", "top10_lift"):
            self.assertEqual(
                metric_value(self.data["model_summary"], "final_holdout", "logistic", metric),
                get_metric(overview["model_summary"], "final_holdout", "logistic", metric),
            )

    def test_prevalence_is_the_ap_reference_and_model_metrics_are_fixed(self):
        summary = self.data["model_summary"]
        prevalence = metric_value(summary, "final_holdout", "logistic", "prevalence")
        benchmark_ap = metric_value(summary, "final_holdout", "prevalence_benchmark", "AP")
        self.assertAlmostEqual(prevalence, benchmark_ap, places=8)
        self.assertGreater(metric_value(summary, "development_oof", "logistic", "AP"), prevalence)
        comparison = build_performance_model_chart(summary)
        self.assertEqual(len(comparison.data), 9)
        self.assertIn("Brier score (lower)", comparison.layout.annotations[-1].text)
        self.assertAlmostEqual(metric_value(summary, "final_holdout", "logistic", "AP"), 0.404225, places=6)

    def test_curve_and_calibration_inputs_are_valid_and_fixed(self):
        predictions = self.data["predictions"]
        pr = build_pr_curve(predictions, "final_holdout", prevalence=metric_value(self.data["model_summary"], "final_holdout", "logistic", "prevalence"))
        pr_hgb = build_pr_curve(predictions, "final_holdout", include_sensitivity=True)
        roc = build_roc_curve(predictions, "development_oof", include_sensitivity=True)
        self.assertEqual(len(pr.data), 1)
        self.assertEqual(len(pr_hgb.data), 2)
        self.assertEqual(len(roc.data), 3)
        self.assertEqual(float(roc.data[0].x[0]), 0.0)
        self.assertEqual(float(roc.data[0].y[-1]), 1.0)
        self.assertTrue(any("No-information prevalence" in annotation.text for annotation in pr.layout.annotations))

        reliability = build_reliability_chart(self.data["calibration"], "final_holdout", include_sensitivity=True)
        self.assertEqual(len(reliability.data), 3)
        self.assertEqual(reliability.data[1].name, "Logistic regression (primary)")
        bad = dict(self.data)
        bad["calibration"] = self.data["calibration"].iloc[0:0].copy()
        with self.assertRaisesRegex(PerformanceDataError, "dashboard_calibration"):
            validate_performance_data(bad)

    def test_required_metric_year_and_sector_contracts_fail_clearly(self):
        missing_metric = dict(self.data)
        missing_metric["model_summary"] = self.data["model_summary"].loc[
            ~((self.data["model_summary"].dataset_split == "development_oof")
              & (self.data["model_summary"].model == "logistic")
              & (self.data["model_summary"].metric == "AP"))
        ].copy()
        with self.assertRaisesRegex(PerformanceDataError, "development_oof/logistic/AP"):
            validate_performance_data(missing_metric)

        missing_year = dict(self.data)
        missing_year["model_by_year"] = self.data["model_by_year"].iloc[0:0].copy()
        with self.assertRaisesRegex(PerformanceDataError, "model_by_year"):
            validate_performance_data(missing_year)

        missing_sector_flag = dict(self.data)
        missing_sector_flag["model_by_sector"] = self.data["model_by_sector"].drop(columns="sufficient_sample_flag")
        with self.assertRaisesRegex(PerformanceDataError, "sufficient_sample_flag"):
            validate_performance_data(missing_sector_flag)

    def test_lift_reference_and_concentration_table_use_frozen_metrics(self):
        summary = self.data["model_summary"]
        chart = build_lift_comparison_chart(summary)
        table = build_risk_concentration_table(summary)
        self.assertEqual(len(chart.data), 2)
        self.assertEqual(len(table), 9)
        logistic_top10 = table.query("Model == 'Logistic regression (primary)' and `Top-risk fraction` == 0.1").iloc[0]
        self.assertEqual(logistic_top10["Selected N (ceiling rule)"], 1031)
        self.assertAlmostEqual(logistic_top10["Lift"], metric_value(summary, "final_holdout", "logistic", "top10_lift"))
        self.assertAlmostEqual(logistic_top10["Observed gap prevalence (lift x overall)"], logistic_top10["Lift"] * logistic_top10["Overall prevalence"])
        self.assertTrue(any(shape.y0 == 1 and shape.y1 == 1 for shape in chart.layout.shapes))

    def test_year_sequence_is_finalized_and_temporal_chart_is_valid(self):
        rows = self.data["model_by_year"].query("dataset_split == 'final_holdout' and model == 'logistic'")
        pairs = tuple(zip(rows.predictor_year.astype(int), rows.target_year.astype(int)))
        self.assertEqual(pairs, EXPECTED_HOLDOUT_PAIRS)
        chart = build_performance_by_year_chart(self.data["model_by_year"])
        self.assertEqual(len(chart.data), 6)
        self.assertIn("target year", chart.layout.title.text)

    def test_msa_size_groups_and_sector_suppression_are_preserved(self):
        size_chart = build_msa_size_performance_chart(self.data["model_by_msa_size"])
        sector_chart = build_sector_performance_chart(self.data["model_by_sector"])
        sector = build_sector_performance_table(self.data["model_by_sector"])
        self.assertEqual(len(size_chart.data), 6)
        self.assertEqual(len(sector_chart.data), 1)
        self.assertEqual(len(sector), 19)
        insufficient = sector.loc[~sector["Sufficient sample"]]
        self.assertEqual(len(insufficient), 2)
        self.assertTrue(insufficient[["AP", "ROC-AUC"]].isna().all().all())
        self.assertTrue(sector_chart.layout.title.text.endswith("sufficient samples only)"))

    def test_every_performance_figure_is_a_nonempty_plotly_chart(self):
        data = self.data
        figures = (
            build_metric_comparison_chart(data["model_summary"]),
            build_performance_model_chart(data["model_summary"]),
            build_pr_curve(data["predictions"], "final_holdout"),
            build_roc_curve(data["predictions"], "final_holdout"),
            build_calibration_chart(data["calibration"]),
            build_reliability_chart(data["calibration"], "final_holdout"),
            build_lift_comparison_chart(data["model_summary"]),
            build_performance_by_year_chart(data["model_by_year"]),
            build_msa_size_performance_chart(data["model_by_msa_size"]),
            build_sector_performance_chart(data["model_by_sector"]),
        )
        self.assertTrue(all(hasattr(figure, "data") and len(figure.data) > 0 for figure in figures))

    def test_page_does_not_fit_models_or_tune_thresholds(self):
        page = Path(__file__).parents[1] / "src/regional_entrepreneurship_intelligence/dashboard/pages/performance.py"
        data_module = page.parents[1] / "performance_data.py"
        chart_module = page.parents[1] / "charts.py"
        for path in (page, data_module, chart_module):
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn(".fit(", text)
            self.assertNotIn("gridsearchcv", text)
            self.assertNotIn("threshold tuning", text)
            self.assertNotIn("sqlite", text)


if __name__ == "__main__":
    unittest.main()
