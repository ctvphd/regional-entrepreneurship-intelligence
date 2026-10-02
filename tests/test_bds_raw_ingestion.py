"""Tests for Assignment 4.5 BDS raw ingestion."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_bds import (
    BDS_SAMPLE_PATH,
    REQUIRED_BDS_COLUMNS,
    load_bds_raw,
    read_bds_csv,
)


class BDSRawIngestionTest(unittest.TestCase):
    def test_bds_sample_loads_raw_rows_idempotently(self) -> None:
        """The permitted official sample loads without duplicate raw facts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "bds_raw.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            create_schema(connection)

            rows = read_bds_csv(BDS_SAMPLE_PATH)
            self.assertEqual(len(rows), 112)
            self.assertTrue(REQUIRED_BDS_COLUMNS.issubset(rows[0]))

            first = load_bds_raw(connection, BDS_SAMPLE_PATH)
            second = load_bds_raw(connection, BDS_SAMPLE_PATH)

            self.assertEqual(first.rows_read, 112)
            self.assertEqual(first.rows_inserted, 112)
            self.assertEqual(first.raw_row_count, 112)
            self.assertEqual(second.rows_inserted, 0)
            self.assertEqual(second.rows_skipped_existing, 112)
            self.assertEqual(second.raw_row_count, 112)

            manifest = connection.execute(
                """
                SELECT source_name, dataset_name, row_count, raw_filename, file_checksum
                FROM metadata_source_manifest
                WHERE manifest_id = ?;
                """,
                (first.manifest_id,),
            ).fetchone()
            self.assertEqual(manifest[0], "Census Business Dynamics Statistics (BDS)")
            self.assertEqual(manifest[1], "Business Dynamics Statistics: MSA by Sector")
            self.assertEqual(manifest[2], 112)
            self.assertEqual(manifest[3], BDS_SAMPLE_PATH.name)
            self.assertEqual(len(manifest[4]), 64)

            raw_row = connection.execute(
                """
                SELECT source_year,
                       source_geography_id,
                       source_industry_id,
                       source_naics_version,
                       is_suppressed,
                       raw_payload
                FROM raw_bds
                WHERE source_row_identifier = 'bds2023_msa_sec|year=2010|msa=10180|sector=11';
                """
            ).fetchone()
            self.assertEqual(raw_row[0:3], (2010, "10180", "11"))
            self.assertIn("source-native sector coding", raw_row[3])
            self.assertEqual(raw_row[4], 1)
            payload = json.loads(raw_row[5])
            self.assertEqual(payload["estabs_exit"], "D")
            self.assertIn("job_creation_births", payload)

            duplicate_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT raw_source_filename, source_row_identifier, COUNT(*) AS row_count
                    FROM raw_bds
                    GROUP BY raw_source_filename, source_row_identifier
                    HAVING row_count > 1
                );
                """
            ).fetchone()[0]
            self.assertEqual(duplicate_count, 0)

            connection.close()


if __name__ == "__main__":
    unittest.main()
