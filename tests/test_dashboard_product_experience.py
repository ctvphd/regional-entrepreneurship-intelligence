from __future__ import annotations

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class DashboardProductExperienceTest(unittest.TestCase):
    def test_overview_uses_three_primary_metrics_and_guided_takeaways(self):
        app = AppTest.from_string(
            "from regional_entrepreneurship_intelligence.dashboard.pages import overview\noverview.render()",
            default_timeout=45,
        ).run()
        self.assertEqual(app.exception, [])
        self.assertEqual({metric.label for metric in app.metric}, {
            "Average Precision", "Top 10% lift", "Evaluation coverage",
        })
        self.assertTrue(any("Three things to know" in item.value for item in app.subheader))
        self.assertTrue(any("Next: Explore Markets" in item.value for item in app.caption))

    def test_explorer_orients_users_without_changing_default_scope(self):
        app = AppTest.from_string(
            "from regional_entrepreneurship_intelligence.dashboard.pages import explorer\nexplorer.render()",
            default_timeout=60,
        ).run()
        self.assertEqual(app.exception, [])
        self.assertTrue(any(item.value == "Start exploring" for item in app.subheader))
        copy = " ".join(item.value for item in (*app.markdown, *app.caption, *app.subheader, *app.info))
        self.assertIn("build a market profile", copy.lower())
        self.assertIsNone(app.get_by_key("selected_msa").value)
        self.assertEqual(app.get_by_key("selected_sectors").value, [])

    def test_quality_and_about_surface_confidence_and_methods(self):
        quality = AppTest.from_string(
            "from regional_entrepreneurship_intelligence.dashboard.pages import quality\nquality.render()",
            default_timeout=60,
        ).run()
        self.assertEqual(quality.exception, [])
        self.assertTrue(any(item.label == "Good comparison coverage" and item.value == "314" for item in quality.metric))
        about = AppTest.from_string(
            "from regional_entrepreneurship_intelligence.dashboard.pages import about\nabout.render()",
            default_timeout=45,
        ).run()
        self.assertEqual(about.exception, [])
        copy = " ".join(item.value for item in (*about.markdown, *about.caption, *about.subheader, *about.text))
        for phrase in ("Measure activity", "Estimate expectation", "Compare the two", "Define the gap", "Evaluate later"):
            self.assertIn(phrase, copy)
        about_source = (Path(__file__).parents[1] / "src/regional_entrepreneurship_intelligence/dashboard/pages/about.py").read_text(encoding="utf-8")
        self.assertIn('st.expander("Technical research question")', about_source)


if __name__ == "__main__":
    unittest.main()
