"""Tests for ACS population growth and lag construction."""

from __future__ import annotations

import unittest

from regional_entrepreneurship_intelligence.etl.transform_acs import (
    compute_lag_values,
    compute_population_growth,
)


class ACSLagTest(unittest.TestCase):
    def test_population_growth_and_lags_respect_calendar_boundaries(self) -> None:
        rows = [
            {
                "geography_id": 1,
                "year": 2020,
                "population": 100.0,
                "median_household_income": 50.0,
                "educational_attainment_pct": 30.0,
                "labor_force_participation_pct": 60.0,
                "unemployment_rate": 4.0,
                "has_suppression": False,
            },
            {
                "geography_id": 1,
                "year": 2021,
                "population": 110.0,
                "median_household_income": 55.0,
                "educational_attainment_pct": 31.0,
                "labor_force_participation_pct": 61.0,
                "unemployment_rate": 5.0,
                "has_suppression": False,
            },
            {
                "geography_id": 1,
                "year": 2023,
                "population": 130.0,
                "median_household_income": 65.0,
                "educational_attainment_pct": 33.0,
                "labor_force_participation_pct": 63.0,
                "unemployment_rate": 6.0,
                "has_suppression": False,
            },
            {
                "geography_id": 2,
                "year": 2021,
                "population": 999.0,
                "median_household_income": 999.0,
                "educational_attainment_pct": 99.0,
                "labor_force_participation_pct": 99.0,
                "unemployment_rate": 9.0,
                "has_suppression": False,
            },
        ]

        growth = compute_population_growth(rows)
        lagged = {
            (row["geography_id"], row["year"]): row
            for row in compute_lag_values(growth)
        }

        self.assertIsNone(lagged[(1, 2020)]["population_growth"])
        self.assertEqual(lagged[(1, 2021)]["population_growth"], 0.1)
        self.assertIsNone(lagged[(1, 2023)]["population_growth"])
        self.assertEqual(lagged[(1, 2021)]["median_household_income_lag1"], 50.0)
        self.assertIsNone(lagged[(1, 2023)]["median_household_income_lag1"])
        self.assertIsNone(lagged[(2, 2021)]["median_household_income_lag1"])


if __name__ == "__main__":
    unittest.main()
