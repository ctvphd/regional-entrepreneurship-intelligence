from __future__ import annotations

import unittest

from streamlit.testing.v1 import AppTest

from regional_entrepreneurship_intelligence.dashboard.data_access import cached_dataset
from regional_entrepreneurship_intelligence.dashboard.pages.quality import _read_report


class DashboardQualityTest(unittest.TestCase):
    def test_frozen_a6_audits_are_available_and_have_expected_contracts(self):
        selection = _read_report("a6_sample_selection_audit.csv")
        complete = _read_report("a6_gap_complete_case_selection.csv")
        geographic = _read_report("a6_geographic_generalization.csv")
        self.assertTrue({"variable", "included_n", "excluded_n", "standardized_difference"}.issubset(selection))
        self.assertTrue({"fold", "split_role", "eligible_exact_pairs", "complete_case_pairs", "inclusion_rate"}.issubset(complete))
        self.assertTrue({"split", "model", "pr_auc", "roc_auc", "msa_n"}.issubset(geographic))
        self.assertIn("pooled_geographic_oof", set(geographic["split"]))

    def test_quality_route_renders_source_backed_sections(self):
        app = AppTest.from_string(
            "from regional_entrepreneurship_intelligence.dashboard.pages import quality\nquality.render()",
            default_timeout=60,
        ).run()
        self.assertEqual(app.exception, [])
        rendered_elements = [
            *app.title, *app.header, *app.subheader, *app.markdown, *app.caption, *app.text,
        ]
        rendered = " ".join(str(element.value) for element in rendered_elements)
        for expected in ("Data Quality & Limitations", "Complete-case selection", "Unseen-MSA test", "Sources used"):
            self.assertIn(expected, rendered)
        self.assertGreaterEqual(len(app.dataframe), 5)

    def test_coverage_and_sector_contracts_keep_expected_rows(self):
        coverage = cached_dataset("coverage")
        sectors = cached_dataset("model_by_sector")
        self.assertEqual(len(coverage), 381)
        self.assertEqual(int(coverage["comparison_eligible_flag"].sum()), 314)
        self.assertEqual(int(((sectors.dataset_split == "final_holdout") & (sectors.model == "logistic")).sum()), 19)
        self.assertGreater(int((~sectors.loc[(sectors.dataset_split == "final_holdout") & (sectors.model == "logistic"), "sufficient_sample_flag"]).sum()), 0)


if __name__ == "__main__":
    unittest.main()
