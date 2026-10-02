"""Tests for BDS startup-rate lag construction."""

from __future__ import annotations

import unittest

from regional_entrepreneurship_intelligence.etl.transform_bds import compute_lag_values


class BDSLagTest(unittest.TestCase):
    def test_lags_respect_group_boundaries_and_calendar_gaps(self) -> None:
        rows = [
            {
                "geography_id": 1,
                "industry_id": 10,
                "year": 2018,
                "startup_rate": 1.0,
                "has_suppression": False,
            },
            {
                "geography_id": 1,
                "industry_id": 10,
                "year": 2020,
                "startup_rate": 3.0,
                "has_suppression": False,
            },
            {
                "geography_id": 2,
                "industry_id": 10,
                "year": 2019,
                "startup_rate": 99.0,
                "has_suppression": False,
            },
            {
                "geography_id": 1,
                "industry_id": 11,
                "year": 2019,
                "startup_rate": 77.0,
                "has_suppression": False,
            },
            {
                "geography_id": 1,
                "industry_id": 10,
                "year": 2021,
                "startup_rate": 4.0,
                "has_suppression": True,
            },
            {
                "geography_id": 1,
                "industry_id": 10,
                "year": 2022,
                "startup_rate": 5.0,
                "has_suppression": False,
            },
        ]

        lagged = {
            (row["geography_id"], row["industry_id"], row["year"]): row
            for row in compute_lag_values(rows)
        }

        self.assertIsNone(lagged[(1, 10, 2020)]["startup_rate_lag1"])
        self.assertEqual(lagged[(1, 10, 2020)]["startup_rate_lag2"], 1.0)
        self.assertEqual(lagged[(1, 10, 2021)]["startup_rate_lag1"], 3.0)
        self.assertIsNone(lagged[(1, 10, 2022)]["startup_rate_lag1"])
        self.assertEqual(lagged[(1, 10, 2022)]["startup_rate_lag2"], 3.0)
        self.assertIsNone(lagged[(2, 10, 2019)]["startup_rate_lag1"])
        self.assertIsNone(lagged[(1, 11, 2019)]["startup_rate_lag1"])


if __name__ == "__main__":
    unittest.main()
