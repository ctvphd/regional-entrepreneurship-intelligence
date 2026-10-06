from __future__ import annotations

import ast
import unittest
from pathlib import Path

import plotly.graph_objects as go

from regional_entrepreneurship_intelligence.dashboard.charts import build_performance_model_chart
from regional_entrepreneurship_intelligence.dashboard.components import development_holdout_label
from regional_entrepreneurship_intelligence.dashboard.performance_data import load_performance_data
from regional_entrepreneurship_intelligence.dashboard.visual_style import (
    HGB_SENSITIVITY,
    LOGISTIC_PRIMARY,
    PLOTLY_CONFIG,
    apply_dashboard_style,
    format_alignment,
    format_count,
    format_growth,
    format_lift,
    format_probability,
    format_rate,
    format_score,
)


class DashboardVisualsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_performance_data()

    def test_shared_plotly_style_applies_layout_and_responsive_config(self):
        fig = apply_dashboard_style(go.Figure(go.Bar(x=["AP"], y=[0.42])))
        self.assertEqual(fig.layout.paper_bgcolor, "#FFFFFF")
        self.assertEqual(fig.layout.font.size, 13)
        self.assertTrue(PLOTLY_CONFIG["responsive"])
        self.assertFalse(PLOTLY_CONFIG["scrollZoom"])

    def test_primary_model_is_first_and_semantically_prominent(self):
        fig = build_performance_model_chart(self.data["model_summary"], "final_holdout")
        names = [str(trace.name) for trace in fig.data]
        logistic_index = next(i for i, name in enumerate(names) if "Logistic regression (primary)" in name)
        hgb_index = next(i for i, name in enumerate(names) if "HistGradientBoosting (sensitivity)" in name)
        self.assertLess(logistic_index, hgb_index)
        self.assertEqual(fig.data[logistic_index].marker.color, LOGISTIC_PRIMARY)
        self.assertEqual(fig.data[hgb_index].marker.color, HGB_SENSITIVITY)
        self.assertEqual(fig.layout.title.text, "Fixed Final temporal holdout model comparison")

    def test_shared_display_formats_follow_dashboard_precision(self):
        self.assertEqual(format_probability(0.12345), "12.3%")
        self.assertEqual(format_rate(2.345), "2.35%")
        self.assertEqual(format_growth(-0.01234), "-1.2%")
        self.assertEqual(format_alignment(-0.234), "-0.23 pp")
        self.assertEqual(format_score(0.123456), "0.123")
        self.assertEqual(format_lift(1.2345), "1.23×")
        self.assertEqual(format_count(12345), "12,345")

    def test_evaluation_labels_are_canonical(self):
        self.assertEqual(development_holdout_label("development_oof"), "Development OOF")
        self.assertEqual(development_holdout_label("final_holdout"), "Final temporal holdout")

    def test_dashboard_chart_layer_does_not_import_estimators_or_mapping_libraries(self):
        root = Path(__file__).resolve().parents[1] / "src" / "regional_entrepreneurship_intelligence" / "dashboard"
        tree = ast.parse((root / "charts.py").read_text(encoding="utf-8"))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("geopandas", imported)
        self.assertNotIn("mapbox", imported)
        self.assertFalse(any(name in imported for name in ("RandomForestClassifier", "LogisticRegression", "HistGradientBoostingClassifier")))


if __name__ == "__main__":
    unittest.main()
