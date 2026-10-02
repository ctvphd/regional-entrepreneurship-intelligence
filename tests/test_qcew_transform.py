"""Tests for QCEW staging and intermediate construction."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.transform_qcew import (
    build_qcew_standardized_layers,
)


class QCEWTransformTest(unittest.TestCase):
    def test_qcew_transform_builds_layers_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "qcew_transform.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            create_schema(connection)

            first = build_qcew_standardized_layers(connection)
            second = build_qcew_standardized_layers(connection)

            self.assertEqual(first.staged_rows, 8)
            self.assertEqual(first.intermediate_rows, 8)
            self.assertEqual(first.rejected_rows, 12)
            self.assertEqual(second.staged_rows, 8)
            self.assertEqual(second.intermediate_rows, 8)
            self.assertEqual(second.duplicate_staging_keys, 0)
            self.assertEqual(second.duplicate_intermediate_keys, 0)

            staged = connection.execute(
                """
                SELECT standardized_cbsa_code,
                       standardized_sector_code,
                       year,
                       employment,
                       establishments,
                       payroll,
                       average_pay,
                       counties_expected,
                       counties_observed,
                       counties_suppressed,
                       is_complete_county_coverage,
                       is_suppressed
                FROM stg_qcew
                WHERE standardized_cbsa_code = '10180'
                  AND standardized_sector_code = '23'
                  AND year = 2022;
                """
            ).fetchone()
            self.assertEqual(staged[0:3], ("10180", "23", 2022))
            self.assertEqual(staged[3], 3706.0)
            self.assertEqual(staged[4], 435.0)
            self.assertEqual(staged[5], 216271465.0)
            self.assertEqual(staged[6], round(216271465.0 / 3706.0))
            self.assertEqual(staged[7:12], (3, 3, 0, 1, 0))

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
            self.assertEqual(rejection_counts, {"excluded_ownership": 6, "unresolved_industry": 6})

            connection.close()


if __name__ == "__main__":
    unittest.main()
