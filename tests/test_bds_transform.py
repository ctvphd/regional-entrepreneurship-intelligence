"""Tests for BDS staging and entrepreneurship construction."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.transform_bds import (
    build_bds_standardized_layers,
)


class BDSTransformTest(unittest.TestCase):
    def test_bds_transform_builds_staging_and_intermediate_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "bds_transform.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            create_schema(connection)

            first = build_bds_standardized_layers(connection)
            second = build_bds_standardized_layers(connection)

            self.assertEqual(first.staged_rows, 112)
            self.assertEqual(second.staged_rows, 112)
            self.assertEqual(first.intermediate_rows, 104)
            self.assertEqual(second.intermediate_rows, 104)
            self.assertEqual(second.duplicate_staging_keys, 0)
            self.assertEqual(second.duplicate_intermediate_keys, 0)
            self.assertEqual(second.missing_startup_measure_rows, 8)

            staged = connection.execute(
                """
                SELECT source_fagecoarse,
                       geography_mapping_status,
                       industry_mapping_status,
                       firm_startups,
                       startup_rate,
                       establishment_entry_rate
                FROM stg_bds
                WHERE source_geography_id = '10180'
                  AND source_industry_id = '23'
                  AND year = 2010;
                """
            ).fetchone()
            self.assertEqual(staged[0], "a) 0")
            self.assertEqual(staged[1], "direct_match")
            self.assertEqual(staged[2], "directly_comparable")
            self.assertEqual(staged[3], 20.0)
            self.assertIsNotNone(staged[4])
            self.assertEqual(staged[5], 9.655)

            int_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM int_entrepreneurship
                WHERE startup_rate IS NOT NULL
                  AND geography_mapping_status = 'direct_match'
                  AND industry_mapping_status = 'directly_comparable';
                """
            ).fetchone()[0]
            self.assertEqual(int_count, 104)

            connection.close()


if __name__ == "__main__":
    unittest.main()
