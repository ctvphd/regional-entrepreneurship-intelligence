"""Tests for QCEW industry growth calculations."""

from __future__ import annotations

import unittest

from regional_entrepreneurship_intelligence.etl.transform_qcew import (
    compute_growth_rate,
    compute_growth_values,
)


class QCEWGrowthTest(unittest.TestCase):
    def test_growth_rates_handle_gaps_zeroes_suppression_and_boundaries(self) -> None:
        self.assertEqual(compute_growth_rate(110.0, 100.0), 0.1)
        self.assertIsNone(compute_growth_rate(110.0, 0.0))
        self.assertIsNone(compute_growth_rate(110.0, None))

        rows = [
            {
                "geography_id": 1,
                "industry_id": 10,
                "year": 2020,
                "employment": 100.0,
                "establishments": 10.0,
                "payroll": 1000.0,
                "average_wage": 10.0,
                "has_suppression": False,
            },
            {
                "geography_id": 1,
                "industry_id": 10,
                "year": 2021,
                "employment": 110.0,
                "establishments": 11.0,
                "payroll": 1210.0,
                "average_wage": 11.0,
                "has_suppression": False,
            },
            {
                "geography_id": 1,
                "industry_id": 10,
                "year": 2023,
                "employment": 120.0,
                "establishments": 12.0,
                "payroll": 1440.0,
                "average_wage": 12.0,
                "has_suppression": False,
            },
            {
                "geography_id": 2,
                "industry_id": 10,
                "year": 2021,
                "employment": 999.0,
                "establishments": 999.0,
                "payroll": 999.0,
                "average_wage": 999.0,
                "has_suppression": False,
            },
            {
                "geography_id": 1,
                "industry_id": 11,
                "year": 2021,
                "employment": 888.0,
                "establishments": 888.0,
                "payroll": 888.0,
                "average_wage": 888.0,
                "has_suppression": False,
            },
            {
                "geography_id": 3,
                "industry_id": 10,
                "year": 2020,
                "employment": 100.0,
                "establishments": 10.0,
                "payroll": 1000.0,
                "average_wage": 10.0,
                "has_suppression": True,
            },
            {
                "geography_id": 3,
                "industry_id": 10,
                "year": 2021,
                "employment": 120.0,
                "establishments": 12.0,
                "payroll": 1440.0,
                "average_wage": 12.0,
                "has_suppression": False,
            },
        ]

        growth = {
            (row["geography_id"], row["industry_id"], row["year"]): row
            for row in compute_growth_values(rows)
        }

        self.assertAlmostEqual(growth[(1, 10, 2021)]["employment_growth"], 0.1)
        self.assertAlmostEqual(growth[(1, 10, 2021)]["payroll_growth"], 0.21)
        self.assertIsNone(growth[(1, 10, 2020)]["employment_growth"])
        self.assertIsNone(growth[(1, 10, 2023)]["employment_growth"])
        self.assertIsNone(growth[(2, 10, 2021)]["employment_growth"])
        self.assertIsNone(growth[(1, 11, 2021)]["employment_growth"])
        self.assertIsNone(growth[(3, 10, 2021)]["employment_growth"])


if __name__ == "__main__":
    unittest.main()
