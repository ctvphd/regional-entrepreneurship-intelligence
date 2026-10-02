"""Tests for Assignment 4.7 QCEW raw ingestion."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_qcew import (
    QCEW_SAMPLE_PATH,
    REQUIRED_QCEW_COLUMNS,
    load_qcew_raw,
    read_qcew_csv,
)


class QCEWRawIngestionTest(unittest.TestCase):
    def test_qcew_sample_loads_raw_rows_idempotently(self) -> None:
        """The permitted official QCEW sample loads without duplicate facts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "qcew_raw.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            create_schema(connection)

            rows = read_qcew_csv(QCEW_SAMPLE_PATH)
            self.assertEqual(len(rows), 36)
            self.assertTrue(REQUIRED_QCEW_COLUMNS.issubset(rows[0]))
            self.assertTrue(any(row["disclosure_code"] == "N" for row in rows))

            first = load_qcew_raw(connection, QCEW_SAMPLE_PATH)
            second = load_qcew_raw(connection, QCEW_SAMPLE_PATH)

            self.assertEqual(first.rows_read, 36)
            self.assertEqual(first.rows_inserted, 36)
            self.assertEqual(first.raw_row_count, 36)
            self.assertEqual(first.suppressed_or_status_row_count, 6)
            self.assertEqual(second.rows_inserted, 0)
            self.assertEqual(second.rows_skipped_existing, 36)
            self.assertEqual(second.raw_row_count, 36)

            manifest = connection.execute(
                """
                SELECT source_name, dataset_name, row_count, raw_filename, file_checksum
                FROM metadata_source_manifest
                WHERE manifest_id = ?;
                """,
                (first.manifest_id,),
            ).fetchone()
            self.assertEqual(
                manifest[0],
                "BLS Quarterly Census of Employment and Wages (QCEW)",
            )
            self.assertEqual(manifest[1], "QCEW NAICS-Based Annual CSV Data, Area Slices")
            self.assertEqual(manifest[2], 36)
            self.assertEqual(manifest[3], QCEW_SAMPLE_PATH.name)
            self.assertEqual(len(manifest[4]), 64)

            raw_row = connection.execute(
                """
                SELECT source_year,
                       source_geography_id,
                       source_industry_id,
                       source_ownership_code,
                       annual_avg_emplvl,
                       total_annual_wages,
                       avg_annual_pay,
                       is_suppressed,
                       raw_payload
                FROM raw_qcew
                WHERE source_row_identifier =
                    'qcew_annual_area|year=2022|area=48059|own=5|industry=23|size=0|qtr=A';
                """
            ).fetchone()
            self.assertEqual(raw_row[0:4], (2022, "48059", "23", "5"))
            self.assertEqual(raw_row[4], "375")
            self.assertEqual(raw_row[7], 0)
            payload = json.loads(raw_row[8])
            self.assertEqual(payload["avg_annual_pay"], "72706")

            status_row_count = connection.execute(
                "SELECT COUNT(*) FROM raw_qcew WHERE is_suppressed = 1;"
            ).fetchone()[0]
            self.assertEqual(status_row_count, 6)

            duplicate_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT raw_source_filename, source_row_identifier, COUNT(*) AS row_count
                    FROM raw_qcew
                    GROUP BY raw_source_filename, source_row_identifier
                    HAVING row_count > 1
                );
                """
            ).fetchone()[0]
            self.assertEqual(duplicate_count, 0)

            connection.close()


if __name__ == "__main__":
    unittest.main()
