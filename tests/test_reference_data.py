"""Tests for Assignment 4.3 reference-table seed data."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.reference import (
    APPROVED_SOURCES,
    get_reference_counts,
    list_approved_source_names,
    seed_reference_data,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema


class ReferenceDataTest(unittest.TestCase):
    def test_reference_seed_data_is_deterministic_and_limited(self) -> None:
        """A4.3 seeds only verified year/source references."""
        with tempfile.TemporaryDirectory() as tmpdir:
            database_path = Path(tmpdir) / "reference_test.sqlite"
            connection = sqlite3.connect(database_path)
            connection.execute("PRAGMA foreign_keys = ON;")

            create_schema(connection)
            seed_reference_data(connection)
            seed_reference_data(connection)

            years = [
                row[0]
                for row in connection.execute(
                    """
                    SELECT year
                    FROM ref_year
                    WHERE is_primary_study_year = 1
                    ORDER BY year;
                    """
                )
            ]
            self.assertEqual(years, list(range(2010, 2024)))
            self.assertEqual(len(years), 14)
            self.assertEqual(len(years), len(set(years)))
            self.assertNotIn(2009, years)
            self.assertNotIn(2024, years)

            sources = connection.execute(
                """
                SELECT source_name, source_agency, dataset_name, homepage_url
                FROM ref_source
                ORDER BY source_name;
                """
            ).fetchall()
            expected_names = sorted(list_approved_source_names())
            self.assertEqual([row[0] for row in sources], expected_names)
            self.assertEqual(len(sources), 4)
            self.assertEqual(len({row[0] for row in sources}), 4)
            self.assertEqual(len(APPROVED_SOURCES), 4)
            self.assertTrue(all(row[1] for row in sources))
            self.assertTrue(all(row[2] for row in sources))
            self.assertTrue(all(row[3] is None for row in sources))

            counts = get_reference_counts(connection)
            self.assertEqual(counts["ref_year"], 14)
            self.assertEqual(counts["ref_source"], 4)
            self.assertEqual(counts["ref_geography"], 0)
            self.assertEqual(counts["ref_industry"], 0)

            connection.close()


if __name__ == "__main__":
    unittest.main()
