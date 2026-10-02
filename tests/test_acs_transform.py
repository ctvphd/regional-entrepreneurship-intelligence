"""Tests for ACS staging and regional-control construction."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.transform_acs import (
    build_acs_regional_controls,
)


class ACSTransformTest(unittest.TestCase):
    def test_acs_transform_builds_regional_controls_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "acs_transform.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            try:
                create_schema(connection)

                first = build_acs_regional_controls(connection)
                second = build_acs_regional_controls(connection)

                self.assertEqual(first.staged_rows, 12)
                self.assertEqual(first.intermediate_rows, 12)
                self.assertEqual(first.rejected_rows, 0)
                self.assertEqual(second.staged_rows, 12)
                self.assertEqual(second.intermediate_rows, 12)
                self.assertEqual(second.duplicate_staging_keys, 0)
                self.assertEqual(second.duplicate_intermediate_keys, 0)

                staged = connection.execute(
                    """
                    SELECT standardized_cbsa_code,
                           year,
                           population,
                           population_moe,
                           median_household_income,
                           educational_attainment_pct,
                           labor_force_participation_pct,
                           unemployment_rate,
                           geography_mapping_status,
                           is_missing
                    FROM stg_acs
                    WHERE standardized_cbsa_code = '10180'
                      AND year = 2020;
                    """
                ).fetchone()
                self.assertEqual(staged[0:3], ("10180", 2020, 171354.0))
                self.assertIsNone(staged[3])
                self.assertEqual(staged[4], 54857.0)
                self.assertEqual(staged[5], 24.4)
                self.assertEqual(staged[6], 61.1)
                self.assertEqual(staged[7], 3.3)
                self.assertEqual(staged[8:10], ("direct_match", 0))

                int_row = connection.execute(
                    """
                    SELECT population_growth,
                           median_household_income_lag1
                    FROM int_regional_controls
                    WHERE standardized_cbsa_code = '10180'
                      AND year = 2021;
                    """
                ).fetchone()
                self.assertAlmostEqual(int_row[0], (175241.0 - 171354.0) / 171354.0)
                self.assertEqual(int_row[1], 54857.0)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
