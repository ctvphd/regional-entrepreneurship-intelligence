"""Tests for QCEW growth lag construction."""

from __future__ import annotations

import unittest

from regional_entrepreneurship_intelligence.etl.transform_qcew import compute_lag_values


class QCEWLagTest(unittest.TestCase):
    def test_lags_respect_calendar_years_and_panel_boundaries(self) -> None:
        rows = [
            {
                "geography_id": 1,
                "industry_id": 10,
                "year": 2019,
                "employment_growth": 0.1,
                "establishment_growth": 0.2,
                "payroll_growth": 0.3,
                "wage_growth": 0.4,
                "has_suppression": False,
            },
            {
                "geography_id": 1,
                "industry_id": 10,
                "year": 2020,
                "employment_growth": 0.5,
                "establishment_growth": 0.6,
                "payroll_growth": 0.7,
                "wage_growth": 0.8,
                "has_suppression": False,
            },
            {
                "geography_id": 1,
                "industry_id": 10,
                "year": 2022,
                "employment_growth": 0.9,
                "establishment_growth": 1.0,
                "payroll_growth": 1.1,
                "wage_growth": 1.2,
                "has_suppression": False,
            },
            {
                "geography_id": 1,
                "industry_id": 10,
                "year": 2023,
                "employment_growth": 1.3,
                "establishment_growth": 1.4,
                "payroll_growth": 1.5,
                "wage_growth": 1.6,
                "has_suppression": True,
            },
            {
                "geography_id": 1,
                "industry_id": 10,
                "year": 2024,
                "employment_growth": 1.7,
                "establishment_growth": 1.8,
                "payroll_growth": 1.9,
                "wage_growth": 2.0,
                "has_suppression": False,
            },
            {
                "geography_id": 2,
                "industry_id": 10,
                "year": 2020,
                "employment_growth": 99.0,
                "establishment_growth": 99.0,
                "payroll_growth": 99.0,
                "wage_growth": 99.0,
                "has_suppression": False,
            },
        ]

        lagged = {
            (row["geography_id"], row["industry_id"], row["year"]): row
            for row in compute_lag_values(rows)
        }

        self.assertEqual(lagged[(1, 10, 2020)]["employment_growth_lag1"], 0.1)
        self.assertEqual(lagged[(1, 10, 2022)]["employment_growth_lag2"], 0.5)
        self.assertIsNone(lagged[(1, 10, 2022)]["employment_growth_lag1"])
        self.assertEqual(lagged[(1, 10, 2022)]["establishment_growth_lag3"], 0.2)
        self.assertEqual(lagged[(1, 10, 2023)]["payroll_growth_lag1"], 1.1)
        self.assertIsNone(lagged[(1, 10, 2024)]["employment_growth_lag1"])
        self.assertIsNone(lagged[(2, 10, 2020)]["employment_growth_lag1"])


if __name__ == "__main__":
    unittest.main()
