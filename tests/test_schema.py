"""Smoke tests for the Assignment 4 SQLite schema."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.schema import create_schema


EXPECTED_TABLES = {
    "ref_geography",
    "ref_industry",
    "ref_year",
    "ref_source",
    "ref_geography_county_crosswalk",
    "metadata_source_manifest",
    "metadata_pipeline_run",
    "raw_bds",
    "raw_bds_firm_age",
    "raw_qcew",
    "raw_cbp",
    "raw_acs",
    "stg_bds",
    "stg_qcew",
    "stg_cbp",
    "stg_acs",
    "int_entrepreneurship",
    "int_industry_growth",
    "int_regional_controls",
    "int_business_structure",
    "analytics_msa_industry_year",
    "quality_rejected_record",
    "quality_table_metric",
}


EXPECTED_INDEXES = {
    "idx_ref_geography_cbsa",
    "idx_ref_geography_county_cbsa",
    "idx_ref_geography_county_geoid",
    "idx_ref_industry_naics",
    "idx_raw_bds_firm_age_source_keys",
    "idx_stg_bds_grain",
    "idx_stg_qcew_grain",
    "idx_stg_cbp_grain",
    "idx_stg_acs_grain",
    "idx_analytics_year",
}


class SchemaSmokeTest(unittest.TestCase):
    def test_schema_creation_is_idempotent(self) -> None:
        """The schema can be created twice and contains expected objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            database_path = Path(tmpdir) / "schema_test.sqlite"
            connection = sqlite3.connect(database_path)
            connection.execute("PRAGMA foreign_keys = ON;")

            create_schema(connection)
            create_schema(connection)

            foreign_keys_enabled = connection.execute("PRAGMA foreign_keys;").fetchone()[0]
            self.assertEqual(foreign_keys_enabled, 1)

            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table';"
                )
            }
            self.assertTrue(EXPECTED_TABLES.issubset(tables))

            indexes = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index';"
                )
            }
            self.assertTrue(EXPECTED_INDEXES.issubset(indexes))

            primary_year_count = connection.execute(
                "SELECT COUNT(*) FROM ref_year WHERE is_primary_study_year = 1;"
            ).fetchone()[0]
            self.assertEqual(primary_year_count, 14)

            fk_count = connection.execute("PRAGMA foreign_key_list(stg_bds);").fetchall()
            self.assertGreaterEqual(len(fk_count), 5)

            connection.close()


if __name__ == "__main__":
    unittest.main()
