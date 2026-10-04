from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.analysis.eda import (
    build_correlation_matrix,
    calculate_pairwise_relationship,
    fit_exploratory_regression,
    run_covid_sensitivity,
    run_outlier_sensitivity,
    summarize_lag_relationships,
    summarize_quadrant_context,
    summarize_sector_relationships,
)
from regional_entrepreneurship_intelligence.analysis.run_relationships import _quadrant_panel_context


class EDARelationshipsTest(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(42)
        rows = []
        for geo in range(3):
            for industry in range(2):
                for year in range(2010, 2024):
                    growth = (year - 2010) / 100 + industry / 100 + rng.normal(0, .01)
                    startup = 5 + 15 * growth + geo * .1 + rng.normal(0, .2)
                    rows.append({
                        "geography_id": geo, "industry_id": industry, "year": year,
                        "sector_code": str(10 + industry), "employment_growth": growth,
                        "startup_rate": startup, "startup_rate_lag1": startup - .2,
                        "startup_rate_lag2": startup - .4, "startup_rate_lag3": startup - .6,
                        "acs_population_growth": .01 + geo * .001,
                    })
        self.frame = pd.DataFrame(rows)

    def test_pairwise_correlation_range_and_available_case_n(self) -> None:
        data = self.frame.copy()
        data.loc[0, "startup_rate"] = np.nan
        result = calculate_pairwise_relationship(data, "employment_growth", "startup_rate", "pearson")
        self.assertEqual(result["n"], len(data) - 1)
        self.assertGreaterEqual(result["coefficient"], -1)
        self.assertLessEqual(result["coefficient"], 1)
        self.assertGreater(result["coefficient"], .9)

    def test_correlation_matrix_contains_only_requested_variables(self) -> None:
        result = build_correlation_matrix(self.frame, ("startup_rate", "employment_growth"))
        self.assertEqual(set(result.columns), {"startup_rate", "employment_growth"})
        self.assertAlmostEqual(result.loc["startup_rate", "startup_rate"], 1)

    def test_sector_summary_covers_observed_sectors(self) -> None:
        result = summarize_sector_relationships(self.frame)
        self.assertEqual(set(result.sector_code), {"10", "11"})
        self.assertTrue((result.n == 42).all())

    def test_lag_relationships_use_only_observed_lags(self) -> None:
        result = summarize_lag_relationships(self.frame)
        self.assertEqual(set(result.lag), {1, 2, 3})
        self.assertTrue((result.n == len(self.frame)).all())
        self.assertTrue(result.coefficient.between(-1, 1).all())

    def test_sensitivities_use_expected_years_and_do_not_mutate(self) -> None:
        before = self.frame.copy(deep=True)
        result = run_covid_sensitivity(self.frame)
        excluded = result[result.method.eq("pearson")].set_index("sensitivity").excluded_years.to_dict()
        self.assertEqual(excluded, {"full": "", "exclude_2020": "2020", "exclude_2020_2021": "2020,2021"})
        self.assertEqual(result[result.sensitivity.eq("full")].n.iloc[0], len(self.frame))
        outlier = run_outlier_sensitivity(self.frame)
        self.assertLess(outlier[outlier.sensitivity.eq("exclude_employment_growth_p01_p99")].n.iloc[0], len(self.frame))
        pd.testing.assert_frame_equal(self.frame, before)

    def test_exploratory_regression_uses_only_requested_terms(self) -> None:
        result = fit_exploratory_regression(
            self.frame, "startup_rate", ("employment_growth",), categorical=("year",),
            model_name="year_controls",
        )
        self.assertIn("employment_growth", set(result.term))
        self.assertFalse(any("gap" in term or "target" in term for term in result.term))
        self.assertTrue((result.n == len(self.frame)).all())
        self.assertTrue((result.covariance == "panel_clustered").all())

    def test_quadrant_acs_context_counts_each_msa_year_once_per_group(self) -> None:
        rows = self.frame.copy()
        rows["establishment_growth"] = rows.employment_growth
        rows["payroll_growth"] = rows.employment_growth
        rows["wage_growth"] = rows.employment_growth
        rows["educational_attainment_pct"] = 30.
        rows["median_household_income"] = 50000.
        rows["labor_force_participation_pct"] = 62.
        rows["unemployment_rate"] = 5.
        summary = summarize_quadrant_context(rows)
        self.assertIn("msa_year_count", summary)
        self.assertIn("unemployment_rate_mean", summary)
        self.assertTrue((summary.unemployment_rate_mean == 5).all())

    def test_quadrant_panel_and_msa_year_context_are_distinct_grains(self) -> None:
        rows = pd.DataFrame(
            {
                "geography_id": [1, 2, 3, 4],
                "year": [2020] * 4,
                "sector_code": ["11"] * 4,
                "startup_rate": [1.0, 1.0, 3.0, 3.0],
                "employment_growth": [0.1, 0.3, 0.1, 0.3],
            }
        )
        panel_summary = _quadrant_panel_context(rows)
        msa_year_summary = summarize_quadrant_context(
            rows.assign(
                acs_population_growth=0.01,
                median_household_income=50000.0,
                educational_attainment_pct=30.0,
                labor_force_participation_pct=62.0,
                unemployment_rate=5.0,
            )
        )
        self.assertEqual(int(panel_summary.observation_count.sum()), 4)
        self.assertIn("observation_count", panel_summary)
        self.assertNotIn("msa_year_count", panel_summary)
        self.assertIn("msa_year_count", msa_year_summary)
        self.assertFalse(panel_summary.equals(msa_year_summary))


if __name__ == "__main__":
    unittest.main()
