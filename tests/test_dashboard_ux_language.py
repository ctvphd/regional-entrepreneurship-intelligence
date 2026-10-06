from __future__ import annotations

import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.dashboard.components import coverage_badge
from regional_entrepreneurship_intelligence.dashboard.constants import PAGE_DESCRIPTIONS, PAGE_HEADLINES
from regional_entrepreneurship_intelligence.dashboard.copy import COVERAGE_LABELS, METRIC_PRESENTATION
from regional_entrepreneurship_intelligence.dashboard.glossary import GLOSSARY
from regional_entrepreneurship_intelligence.dashboard.loader import load_filter_options
from regional_entrepreneurship_intelligence.dashboard.overview_data import get_metric, load_overview_data


ROOT = Path(__file__).parents[1]


class DashboardUXLanguageTest(unittest.TestCase):
    def test_navigation_uses_approved_display_labels_without_changing_routes(self):
        app = (ROOT / "src/regional_entrepreneurship_intelligence/dashboard/app.py").read_text(encoding="utf-8")
        for label, route in (
            ("Overview", "overview"),
            ("Explore Markets", "explorer"),
            ("Model Insights", "performance"),
            ("Data & Confidence", "quality"),
            ("About the Analysis", "about"),
        ):
            self.assertIn(f'title="{label}"', app)
            self.assertIn(f'url_path="{route}"', app)

    def test_each_page_has_a_question_led_heading_and_plain_intro(self):
        self.assertEqual(set(PAGE_HEADLINES), set(PAGE_DESCRIPTIONS))
        self.assertTrue(all(title.endswith("?") for title in PAGE_HEADLINES.values()))
        self.assertTrue(all(len(description.split()) < 30 for description in PAGE_DESCRIPTIONS.values()))

    def test_technical_metric_names_and_directions_remain_available(self):
        self.assertIn("Average Precision (AP)", GLOSSARY["AP"])
        self.assertIn("ROC-AUC", GLOSSARY["ROC-AUC"])
        self.assertIn("Brier score", GLOSSARY["Brier"])
        self.assertIn("Lower is better", GLOSSARY["Brier"])
        self.assertIn("Lift", GLOSSARY)
        self.assertIn("Calibration", GLOSSARY)
        self.assertEqual(METRIC_PRESENTATION["AP"]["technical"], "Average Precision (AP)")

    def test_primary_and_sensitivity_model_names_are_preserved(self):
        overview = (ROOT / "src/regional_entrepreneurship_intelligence/dashboard/pages/overview.py").read_text(encoding="utf-8")
        self.assertIn("Logistic regression", overview)
        self.assertIn("HistGradientBoosting", overview)

    def test_gap_and_prediction_language_is_non_deterministic_and_retrospective(self):
        from regional_entrepreneurship_intelligence.dashboard.copy import GAP_PLAIN_LANGUAGE

        self.assertIn("model-relative", GAP_PLAIN_LANGUAGE)
        self.assertIn("not a judgment", GAP_PLAIN_LANGUAGE)
        joined = " ".join(PAGE_DESCRIPTIONS.values()).lower()
        for forbidden in ("will experience a gap", "chance of failure", "current live risk"):
            self.assertNotIn(forbidden, joined)

    def test_coverage_display_maps_but_does_not_replace_canonical_values(self):
        self.assertEqual(set(COVERAGE_LABELS), {"comparison_eligible", "thin"})
        self.assertEqual(coverage_badge("comparison_eligible"), "Good comparison coverage")
        self.assertEqual(coverage_badge("thin"), "Limited data coverage")

    def test_risk_categories_remain_unavailable(self):
        self.assertEqual(load_filter_options()["risk_category_options"], [])

    def test_frozen_metrics_and_horizon_remain_unchanged(self):
        data = load_overview_data()
        self.assertAlmostEqual(get_metric(data["model_summary"], "final_holdout", "logistic", "AP"), 0.404225, places=6)
        self.assertEqual(data["metadata"]["forecast_horizon_years"], 3)
        self.assertEqual(set(data["coverage"]["coverage_status"]), {"comparison_eligible", "thin"})

    def test_all_plotly_pages_use_streamlit_active_theme(self):
        components = (ROOT / "src/regional_entrepreneurship_intelligence/dashboard/components.py").read_text(encoding="utf-8")
        style = (ROOT / "src/regional_entrepreneurship_intelligence/dashboard/visual_style.py").read_text(encoding="utf-8")
        self.assertIn('theme="streamlit"', components)
        self.assertIn('paper_bgcolor="rgba(0,0,0,0)"', style)
        self.assertNotIn('template="plotly_white"', style)

    def test_no_mapping_or_model_fitting_dependency_was_added_to_ui(self):
        dashboard = ROOT / "src/regional_entrepreneurship_intelligence/dashboard"
        for path in [*dashboard.glob("*.py"), *dashboard.joinpath("pages").glob("*.py")]:
            source = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("geopandas", source)
            self.assertNotIn("logisticregression(", source)
            self.assertNotIn("histgradientboostingclassifier(", source)


if __name__ == "__main__":
    unittest.main()
