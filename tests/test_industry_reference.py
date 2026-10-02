"""Tests for authoritative NAICS reference loading."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.reference import (
    NAICS_ANALYTICAL_VERSION,
    load_authoritative_reference_data,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema


class IndustryReferenceTest(unittest.TestCase):
    def test_industry_reference_loads_hierarchy_and_reruns_cleanly(self) -> None:
        """Official Census NAICS structure populates industry references once."""
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "industry_reference.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            create_schema(connection)

            first = load_authoritative_reference_data(connection)
            second = load_authoritative_reference_data(connection)

            self.assertEqual(first.ref_industry_count, 2125)
            self.assertEqual(second.ref_industry_count, 2125)

            level_counts = dict(
                connection.execute(
                    """
                    SELECT naics_level, COUNT(*)
                    FROM ref_industry
                    GROUP BY naics_level;
                    """
                )
            )
            self.assertEqual(level_counts[2], 20)
            self.assertEqual(level_counts[6], 1012)

            manufacturing = connection.execute(
                """
                SELECT naics_level, naics_title, naics_version, parent_naics_code
                FROM ref_industry
                WHERE naics_code = '31-33';
                """
            ).fetchone()
            self.assertEqual(
                manufacturing,
                (2, "Manufacturing", NAICS_ANALYTICAL_VERSION, None),
            )

            crop_production = connection.execute(
                """
                SELECT parent_naics_code
                FROM ref_industry
                WHERE naics_code = '111';
                """
            ).fetchone()[0]
            self.assertEqual(crop_production, "11")

            duplicate_industries = connection.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT naics_code, naics_version, COUNT(*) AS row_count
                    FROM ref_industry
                    GROUP BY naics_code, naics_version
                    HAVING row_count > 1
                );
                """
            ).fetchone()[0]
            self.assertEqual(duplicate_industries, 0)

            invalid_levels = connection.execute(
                """
                SELECT COUNT(*)
                FROM ref_industry
                WHERE naics_level NOT BETWEEN 2 AND 6
                   OR naics_title = ''
                   OR naics_version <> ?;
                """,
                (NAICS_ANALYTICAL_VERSION,),
            ).fetchone()[0]
            self.assertEqual(invalid_levels, 0)

            connection.close()


if __name__ == "__main__":
    unittest.main()
