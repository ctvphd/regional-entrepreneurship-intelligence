"""Tests for Assignment 4.3 metadata and quality helpers."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.metadata import (
    finish_pipeline_run,
    insert_quality_metric,
    insert_rejected_record,
    insert_source_manifest,
    start_pipeline_run,
    update_pipeline_run,
)
from regional_entrepreneurship_intelligence.database.reference import seed_reference_data
from regional_entrepreneurship_intelligence.database.schema import create_schema


class MetadataHelperTest(unittest.TestCase):
    def test_manifest_run_quality_and_rejection_helpers(self) -> None:
        """Metadata helpers write auditable synthetic test records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            database_path = Path(tmpdir) / "metadata_test.sqlite"
            connection = sqlite3.connect(database_path)
            connection.execute("PRAGMA foreign_keys = ON;")
            create_schema(connection)
            seed_reference_data(connection)

            source_id = connection.execute(
                """
                SELECT source_id
                FROM ref_source
                WHERE source_name = 'Census Business Dynamics Statistics (BDS)';
                """
            ).fetchone()[0]

            manifest_id = insert_source_manifest(
                connection,
                source_id=source_id,
                source_name="Census Business Dynamics Statistics (BDS)",
                source_agency="U.S. Census Bureau",
                dataset_name="Business Dynamics Statistics",
                access_method="synthetic unit-test fixture",
                source_year=2023,
                raw_filename="synthetic_bds_2023.csv",
                file_checksum="sha256:test",
                row_count=1,
                notes="Synthetic metadata helper test only.",
            )
            manifest = connection.execute(
                """
                SELECT source_id, source_year, row_count
                FROM metadata_source_manifest
                WHERE manifest_id = ?;
                """,
                (manifest_id,),
            ).fetchone()
            self.assertEqual(manifest, (source_id, 2023, 1))

            run_id = start_pipeline_run(connection, stage="unit_test_extract")
            update_pipeline_run(connection, run_id, records_read=1, records_written=1)
            finish_pipeline_run(
                connection,
                run_id,
                status="success",
                records_rejected=1,
                warnings="Synthetic rejected-record path exercised.",
            )
            run = connection.execute(
                """
                SELECT status, records_read, records_written, records_rejected
                FROM metadata_pipeline_run
                WHERE pipeline_run_id = ?;
                """,
                (run_id,),
            ).fetchone()
            self.assertEqual(run, ("success", 1, 1, 1))

            metric_id = insert_quality_metric(
                connection,
                pipeline_run_id=run_id,
                table_name="stg_bds",
                metric_name="row_count",
                metric_value=1,
                year=2023,
                scope="unit_test",
            )
            metric = connection.execute(
                """
                SELECT table_name, metric_name, metric_value, year, scope
                FROM quality_table_metric
                WHERE metric_id = ?;
                """,
                (metric_id,),
            ).fetchone()
            self.assertEqual(metric, ("stg_bds", "row_count", 1.0, 2023, "unit_test"))

            rejection_id = insert_rejected_record(
                connection,
                pipeline_run_id=run_id,
                source_id=source_id,
                table_name="stg_bds",
                stage="unit_test_transform",
                source_row_identifier="synthetic-row-1",
                reason_code="invalid_year",
                reason_detail="Synthetic record uses an out-of-window year.",
                original_value="2024",
                serialized_record={"year": 2024, "naics": "00"},
            )
            rejected = connection.execute(
                """
                SELECT table_name, stage, reason_code, original_value, serialized_record
                FROM quality_rejected_record
                WHERE rejection_id = ?;
                """,
                (rejection_id,),
            ).fetchone()
            self.assertEqual(
                rejected[0:4],
                ("stg_bds", "unit_test_transform", "invalid_year", "2024"),
            )
            self.assertIn('"year": 2024', rejected[4])

            connection.close()


if __name__ == "__main__":
    unittest.main()
