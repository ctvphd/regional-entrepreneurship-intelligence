"""Tests for the reusable Assignment 5 descriptive helpers."""

from __future__ import annotations

import unittest

import pandas as pd

from regional_entrepreneurship_intelligence.analysis.eda import (
    summarize_economic_plausibility,
    summarize_missingness,
    summarize_missingness_by_year,
    summarize_numeric_variables,
    summarize_structural_missingness,
)


class EDADescriptiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pd.DataFrame(
            {
                "geography_id": [1, 1, 1],
                "industry_id": [2, 2, 2],
                "year": [2010, 2011, 2013],
                "startup_rate": [1.0, 2.0, None],
                "startup_rate_lag1": [None, None, None],
                "bds_has_suppression": [0, 0, 0],
                "bds_startup_available": [1, 1, 1],
                "labor_force_participation_pct": [-1.0, 50.0, 101.0],
                "future_target": [0, 1, 0],
            }
        )

    def test_numeric_summaries_have_ordered_percentiles_and_exclude_targets(self) -> None:
        before = self.frame.copy(deep=True)
        summary = summarize_numeric_variables(self.frame)
        row = summary.set_index("variable").loc["startup_rate"]
        self.assertEqual(row["count"], 2)
        self.assertEqual(row["missing_count"], 1)
        quantiles = [row[name] for name in ("p01", "p05", "p25", "median", "p75", "p95", "p99")]
        self.assertEqual(quantiles, sorted(quantiles))
        self.assertNotIn("future_target", set(summary["variable"]))
        self.assertNotIn("future_target", set(summarize_missingness(self.frame)["variable"]))
        pd.testing.assert_frame_equal(self.frame, before)

    def test_missingness_percentages_and_year_breakdown_are_valid(self) -> None:
        summary = summarize_missingness(self.frame, ["startup_rate"])
        self.assertEqual(summary.loc[0, "missing_count"], 1)
        self.assertAlmostEqual(summary.loc[0, "missing_pct"], 100 / 3)
        yearly = summarize_missingness_by_year(self.frame, ["startup_rate"])
        self.assertTrue(yearly["missing_pct"].between(0, 100).all())
        self.assertEqual(len(yearly), 3)

    def test_lag_missingness_distinguishes_absent_predecessor_from_available(self) -> None:
        causes = summarize_structural_missingness(self.frame, ["startup_rate_lag1"])
        counts = causes.set_index("cause_category")["missing_count"]
        self.assertEqual(counts["expected_structural_missing"], 2)
        self.assertEqual(counts["unexplained_missing"], 1)

    def test_acs_lag_uses_msa_year_predecessor_not_industry_key(self) -> None:
        frame = pd.DataFrame(
            {
                "geography_id": [1, 1, 1],
                "industry_id": [1, 1, 2],
                "year": [2010, 2011, 2012],
                "acs_population_growth_lag1": [None, None, None],
            }
        )
        causes = summarize_structural_missingness(frame, ["acs_population_growth_lag1"])
        counts = causes.set_index("cause_category")["missing_count"]
        self.assertEqual(counts["expected_structural_missing"], 2)
        self.assertEqual(counts["unexplained_missing"], 1)

    def test_cbp_missingness_uses_suppression_coverage_and_match_flags(self) -> None:
        frame = pd.DataFrame(
            {
                "geography_id": [1, 2, 3],
                "industry_id": [1, 1, 1],
                "year": [2012, 2012, 2012],
                "cbp_employment": [None, None, None],
                "cbp_has_suppression": [1, 0, 0],
                "cbp_is_complete_county_coverage": [0, 0, None],
                "cbp_matched": [0, 0, 0],
            }
        )
        causes = summarize_structural_missingness(frame, ["cbp_employment"])
        counts = causes.set_index("cause_category")["missing_count"]
        self.assertEqual(counts["source_data_quality_missing"], 2)
        self.assertEqual(counts["support_source_missing"], 1)

    def test_percentage_range_checks_flag_invalid_values(self) -> None:
        checks = summarize_economic_plausibility(self.frame)
        row = checks.loc[checks.variable == "labor_force_participation_pct"].iloc[0]
        self.assertEqual(row.flagged_count, 2)
        self.assertTrue(checks.loc[checks.variable == "startup_rate", "flagged_count"].iloc[0] == 0)


if __name__ == "__main__":
    unittest.main()
