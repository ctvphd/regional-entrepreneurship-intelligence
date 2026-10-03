from __future__ import annotations

import unittest

import pandas as pd

from regional_entrepreneurship_intelligence.analysis.eda import (
    build_descriptive_quadrants,
    collapse_acs_to_msa_year,
    summarize_by_msa,
    summarize_by_sector,
    summarize_by_year,
    summarize_msa_coverage,
)


class EDAPatternsTest(unittest.TestCase):
    def setUp(self) -> None:
        records = []
        for geo in range(1, 7):
            for sector in ("11", "21"):
                for year in range(2010, 2024):
                    records.append({
                        "geography_id": geo, "industry_id": int(sector), "year": year,
                        "cbsa_code": f"{geo:05d}", "cbsa_name": f"Metro {geo}",
                        "sector_code": sector, "startup_rate": float((geo + (year % 2) * 3) % 6 + 1),
                        "employment_growth": (geo - 3) / 100,
                        "establishment_growth": (geo - 2) / 100,
                        "payroll_growth": (geo - 1) / 100, "wage_growth": geo / 100,
                        "acs_population_growth": .01, "unemployment_rate": 4 + geo / 10,
                        "educational_attainment_pct": 30 + geo,
                        "median_household_income": 50000 + geo,
                        "labor_force_participation_pct": 60 + geo,
                        "startup_rate_lead1": 999,
                    })
        self.frame = pd.DataFrame(records)

    def test_year_summaries_cover_study_window(self) -> None:
        result = summarize_by_year(self.frame, ("startup_rate",))
        self.assertEqual(result.year.tolist(), list(range(2010, 2024)))

    def test_sector_summaries_contain_all_sectors(self) -> None:
        self.assertEqual(set(summarize_by_sector(self.frame, ("startup_rate",)).sector_code), {"11", "21"})

    def test_msa_scope_and_acs_msa_year_collapse(self) -> None:
        collapsed = collapse_acs_to_msa_year(self.frame)
        self.assertEqual(len(collapsed), 6 * 14)
        self.assertEqual(collapsed.groupby("geography_id").size().iloc[0], 14)
        summary = summarize_by_msa(self.frame, ("startup_rate",), min_rows=20, min_sectors=2, min_years=10)
        self.assertEqual(summary.geography_id.nunique(), 6)
        msa1 = summary.loc[(summary.geography_id == 1) & (summary.variable == "startup_rate")].iloc[0]
        self.assertEqual(msa1["median_household_income"], 50001)

    def test_acs_conflicts_within_msa_year_are_rejected(self) -> None:
        bad = self.frame.copy()
        bad.loc[1, "unemployment_rate"] = 99
        with self.assertRaisesRegex(ValueError, "Conflicting repeated"):
            collapse_acs_to_msa_year(bad)

    def test_coverage_rule_is_deterministic_and_retains_full_scope(self) -> None:
        first = summarize_msa_coverage(self.frame, min_rows=20, min_sectors=2, min_years=10)
        second = summarize_msa_coverage(self.frame, min_rows=20, min_sectors=2, min_years=10)
        pd.testing.assert_frame_equal(first, second)
        self.assertTrue(first.eligible_for_comparison.all())
        self.assertEqual(len(summarize_msa_coverage(self.frame, min_rows=1000)), 6)

    def test_quadrants_valid_and_do_not_use_leads_or_mutate_input(self) -> None:
        before = self.frame.copy(deep=True)
        result = build_descriptive_quadrants(self.frame)
        self.assertEqual(set(result.quadrant), {
            "high_growth_high_startup", "high_growth_low_startup",
            "low_growth_high_startup", "low_growth_low_startup",
        })
        self.assertFalse(any("lead" in name or "target" in name or "gap" in name for name in result.columns))
        pd.testing.assert_frame_equal(self.frame, before)
        msa_result = build_descriptive_quadrants(
            self.frame, group_by=("geography_id", "cbsa_code", "cbsa_name")
        )
        self.assertEqual(msa_result.geography_id.nunique(), 6)
        self.assertIn("percent_within_group", result.columns)


if __name__ == "__main__":
    unittest.main()
