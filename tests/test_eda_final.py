from __future__ import annotations

import unittest

import pandas as pd

from regional_entrepreneurship_intelligence.analysis.run_eda import (
    FIGURE_INFO,
    _figure_index,
    _final_report,
    panel_fingerprint,
)


class EDAFinalSynthesisTest(unittest.TestCase):
    def test_final_report_maps_hypotheses_and_excludes_target_construction(self) -> None:
        panel = pd.DataFrame(
            {
                "cbsa_code": ["001", "001"],
                "sector_code": ["11", "21"],
                "year": [2010, 2023],
            }
        )
        report = _final_report(panel)
        for expected in ("H1:", "H2:", "H3:", "H4:", "NOT the entrepreneurial-gap target", "Assignment 6 Handoff"):
            self.assertIn(expected, report)

    def test_figure_index_covers_all_reviewed_figures_with_two_sentence_interpretations(self) -> None:
        index = _figure_index()
        for filename, (_, interpretation, step, caution) in FIGURE_INFO.items():
            self.assertIn(filename, index)
            self.assertIn(f"**Step:** {step}", index)
            self.assertIn(f"**Interpretation:** {interpretation}", index)
            self.assertIn(f"**Caution:** {caution}", index)
            self.assertEqual(interpretation.count(". ") + interpretation.count("! ") + interpretation.count("? ") + 1, 2)
        self.assertEqual(len(FIGURE_INFO), 22)

    def test_panel_fingerprint_is_deterministic_and_sensitive_to_content(self) -> None:
        frame = pd.DataFrame({"year": [2010, 2011], "value": [0.1, 0.2]})
        original = frame.copy(deep=True)
        fingerprint = panel_fingerprint(frame)
        self.assertEqual(fingerprint, panel_fingerprint(frame))
        self.assertTrue(frame.equals(original))
        changed = frame.assign(value=[0.1, 0.3])
        self.assertNotEqual(fingerprint, panel_fingerprint(changed))


if __name__ == "__main__":
    unittest.main()
