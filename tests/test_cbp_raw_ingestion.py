"""Tests for Assignment 4.10 CBP raw ingestion."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_cbp import (
    CBP_SAMPLE_PATH,
    REQUIRED_CBP_COLUMNS,
    load_cbp_raw,
    read_cbp_csv,
)


class CBPRawIngestionTest(unittest.TestCase):
    def test_cbp_sample_loads_raw_rows_idempotently(self) -> None:
        """The official CBP API sample loads without duplicate raw facts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "cbp_raw.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            create_schema(connection)

            rows = read_cbp_csv(CBP_SAMPLE_PATH)
            self.assertEqual(len(rows), 26)
            self.assertTrue(REQUIRED_CBP_COLUMNS.issubset(rows[0]))
            self.assertEqual(
                {row["source_naics_version"] for row in rows},
                {"2017"},
            )

            first = load_cbp_raw(connection, CBP_SAMPLE_PATH)
            second = load_cbp_raw(connection, CBP_SAMPLE_PATH)

            self.assertEqual(first.rows_read, 26)
            self.assertEqual(first.rows_inserted, 26)
            self.assertEqual(first.raw_row_count, 26)
            self.assertEqual(first.flagged_row_count, 0)
            self.assertEqual(second.rows_inserted, 0)
            self.assertEqual(second.rows_skipped_existing, 26)
            self.assertEqual(second.raw_row_count, 26)

            manifest = connection.execute(
                """
                SELECT source_name, dataset_name, row_count, raw_filename, file_checksum
                FROM metadata_source_manifest
                WHERE manifest_id = ?;
                """,
                (first.manifest_id,),
            ).fetchone()
            self.assertEqual(manifest[0], "Census County Business Patterns (CBP)")
            self.assertEqual(manifest[1], "County Business Patterns API")
            self.assertEqual(manifest[2], 26)
            self.assertEqual(manifest[3], CBP_SAMPLE_PATH.name)
            self.assertEqual(len(manifest[4]), 64)

            raw_row = connection.execute(
                """
                SELECT source_year,
                       source_county_geoid,
                       source_industry_id,
                       establishments,
                       employment,
                       annual_payroll,
                       first_quarter_payroll,
                       is_suppressed,
                       raw_payload
                FROM raw_cbp
                WHERE source_row_identifier =
                    'cbp_county|year=2022|county=48059|industry=23|lfo=001|empszes=001';
                """
            ).fetchone()
            self.assertEqual(raw_row[0:3], (2022, "48059", "23"))
            self.assertEqual(raw_row[3], "42")
            self.assertEqual(raw_row[4], "240")
            self.assertEqual(raw_row[7], 0)
            payload = json.loads(raw_row[8])
            self.assertEqual(payload["county_name"], "Callahan County, Texas")
            self.assertNotIn("key=", payload["official_api_url"])

            duplicate_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT raw_source_filename, source_row_identifier, COUNT(*) AS row_count
                    FROM raw_cbp
                    GROUP BY raw_source_filename, source_row_identifier
                    HAVING row_count > 1
                );
                """
            ).fetchone()[0]
            self.assertEqual(duplicate_count, 0)

            connection.close()


if __name__ == "__main__":
    unittest.main()
