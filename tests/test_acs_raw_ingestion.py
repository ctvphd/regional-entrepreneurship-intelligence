"""Tests for Assignment 4.9 ACS raw ingestion."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_acs import (
    ACS_SAMPLE_PATH,
    REQUIRED_ACS_COLUMNS,
    load_acs_raw,
    read_acs_csv,
)


class ACSRawIngestionTest(unittest.TestCase):
    def test_acs_sample_loads_raw_rows_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "acs_raw.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            try:
                create_schema(connection)

                rows = read_acs_csv(ACS_SAMPLE_PATH)
                self.assertEqual(len(rows), 60)
                self.assertTrue(REQUIRED_ACS_COLUMNS.issubset(rows[0]))
                self.assertEqual(rows[0]["variable_id"], "DP05_0001E")
                self.assertEqual(rows[0]["moe_variable_id"], "DP05_0001M")

                first = load_acs_raw(connection, ACS_SAMPLE_PATH)
                second = load_acs_raw(connection, ACS_SAMPLE_PATH)

                self.assertEqual(first.rows_read, 60)
                self.assertEqual(first.rows_inserted, 60)
                self.assertEqual(first.raw_row_count, 60)
                self.assertEqual(second.rows_inserted, 0)
                self.assertEqual(second.rows_skipped_existing, 60)
                self.assertEqual(second.raw_row_count, 60)

                manifest = connection.execute(
                    """
                    SELECT source_name, dataset_name, row_count, raw_filename, file_checksum
                    FROM metadata_source_manifest
                    WHERE manifest_id = ?;
                    """,
                    (first.manifest_id,),
                ).fetchone()
                self.assertEqual(manifest[0], "American Community Survey (ACS)")
                self.assertEqual(manifest[1], "ACS 5-year Data Profile")
                self.assertEqual(manifest[2], 60)
                self.assertEqual(manifest[3], ACS_SAMPLE_PATH.name)
                self.assertEqual(len(manifest[4]), 64)

                raw_row = connection.execute(
                    """
                    SELECT source_year,
                           source_geography_id,
                           source_geography_name,
                           source_variable_id,
                           source_moe_variable_id,
                           estimate_value,
                           margin_of_error,
                           raw_payload
                    FROM raw_acs
                    WHERE source_row_identifier =
                        'acs5_profile|year=2020|geo=10180|variable=DP05_0001E';
                    """
                ).fetchone()
                self.assertEqual(raw_row[0:5], (2020, "10180", "Abilene, TX Metro Area", "DP05_0001E", "DP05_0001M"))
                self.assertEqual(raw_row[5], "171354")
                payload = json.loads(raw_row[7])
                self.assertEqual(payload["control_name"], "population")
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
