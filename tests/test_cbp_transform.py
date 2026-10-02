"""Tests for CBP business-structure construction."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.transform_cbp import (
    build_cbp_business_structure,
)


class CBPTransformTest(unittest.TestCase):
    def test_cbp_transform_builds_layers_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "cbp_transform.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            create_schema(connection)

            first = build_cbp_business_structure(connection)
            second = build_cbp_business_structure(connection)

            self.assertEqual(first.staged_rows, 26)
            self.assertEqual(first.intermediate_rows, 6)
            self.assertEqual(first.rejected_rows, 8)
            self.assertEqual(second.staged_rows, 26)
            self.assertEqual(second.intermediate_rows, 6)
            self.assertEqual(second.duplicate_staging_keys, 0)
            self.assertEqual(second.duplicate_intermediate_keys, 0)
            self.assertEqual(second.flagged_staging_rows, 0)
            self.assertEqual(second.incomplete_aggregation_rows, 2)

            staged = connection.execute(
                """
                SELECT standardized_cbsa_code,
                       standardized_sector_code,
                       year,
                       source_county_geoid,
                       establishments,
                       employment,
                       annual_payroll,
                       first_quarter_payroll,
                       geography_mapping_status,
                       industry_mapping_status,
                       is_suppressed
                FROM stg_cbp
                WHERE source_county_geoid = '48059'
                  AND source_industry_id = '23'
                  AND year = 2022;
                """
            ).fetchone()
            self.assertEqual(staged[0:4], ("10180", "23", 2022, "48059"))
            self.assertEqual(staged[4:8], (42.0, 240.0, 16195.0, 3168.0))
            self.assertEqual(staged[8:11], ("crosswalk_required", "directly_comparable", 0))

            intermediate = connection.execute(
                """
                SELECT standardized_cbsa_code,
                       standardized_sector_code,
                       year,
                       establishments,
                       employment,
                       annual_payroll,
                       first_quarter_payroll,
                       counties_expected,
                       counties_observed,
                       counties_suppressed,
                       is_complete_county_coverage
                FROM int_business_structure
                WHERE standardized_cbsa_code = '10180'
                  AND standardized_sector_code = '23'
                  AND year = 2022;
                """
            ).fetchone()
            self.assertEqual(intermediate[0:3], ("10180", "23", 2022))
            self.assertEqual(intermediate[3:7], (410.0, 3422.0, 201517.0, 42024.0))
            self.assertEqual(intermediate[7:11], (3, 3, 0, 1))

            sector_11_rows = connection.execute(
                """
                SELECT COUNT(*)
                FROM int_business_structure
                WHERE standardized_sector_code = '11';
                """
            ).fetchone()[0]
            self.assertEqual(sector_11_rows, 0)

            rejection_counts = dict(
                connection.execute(
                    """
                    SELECT reason_code, COUNT(*)
                    FROM quality_rejected_record
                    WHERE pipeline_run_id = ?
                    GROUP BY reason_code;
                    """,
                    (second.pipeline_run_id,),
                ).fetchall()
            )
            self.assertEqual(
                rejection_counts,
                {"incomplete_aggregation": 2, "unresolved_industry": 6},
            )

            connection.close()


if __name__ == "__main__":
    unittest.main()
