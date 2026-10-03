"""Tests for authoritative CBSA geography reference loading."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.reference import (
    GEOGRAPHY_VINTAGE,
    OFFICIAL_REFERENCE_ASSETS,
    load_authoritative_reference_data,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema


class GeographyReferenceTest(unittest.TestCase):
    def test_geography_reference_loads_and_reruns_without_duplicates(self) -> None:
        """Official Census CBSA references populate geography tables once."""
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "geography_reference.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            create_schema(connection)

            first = load_authoritative_reference_data(connection)
            second = load_authoritative_reference_data(connection)

            self.assertEqual(first.ref_geography_count, 935)
            self.assertEqual(second.ref_geography_count, 935)
            self.assertEqual(first.ref_geography_county_crosswalk_count, 1915)
            self.assertEqual(second.ref_geography_county_crosswalk_count, 1915)

            geography_types = {
                row[0]
                for row in connection.execute(
                    "SELECT DISTINCT geography_type FROM ref_geography;"
                )
            }
            self.assertEqual(geography_types, {"MSA", "MICROPOLITAN"})

            msa = connection.execute(
                """
                SELECT cbsa_name, geography_type, source_vintage
                FROM ref_geography
                WHERE cbsa_code = '10180';
                """
            ).fetchone()
            self.assertEqual(
                msa,
                ("Abilene, TX", "MSA", GEOGRAPHY_VINTAGE),
            )

            duplicate_geographies = connection.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT cbsa_code, source_vintage, COUNT(*) AS row_count
                    FROM ref_geography
                    GROUP BY cbsa_code, source_vintage
                    HAVING row_count > 1
                );
                """
            ).fetchone()[0]
            self.assertEqual(duplicate_geographies, 0)

            duplicate_counties = connection.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT cbsa_code, county_geoid, source_vintage, COUNT(*) AS row_count
                    FROM ref_geography_county_crosswalk
                    GROUP BY cbsa_code, county_geoid, source_vintage
                    HAVING row_count > 1
                );
                """
            ).fetchone()[0]
            self.assertEqual(duplicate_counties, 0)

            invalid_fk_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM ref_geography_county_crosswalk AS county
                LEFT JOIN ref_geography AS geography
                    ON county.geography_id = geography.geography_id
                WHERE geography.geography_id IS NULL;
                """
            ).fetchone()[0]
            self.assertEqual(invalid_fk_count, 0)

            manifest_count = connection.execute(
                "SELECT COUNT(*) FROM metadata_source_manifest;"
            ).fetchone()[0]
            self.assertEqual(manifest_count, len(OFFICIAL_REFERENCE_ASSETS))

            connection.close()


if __name__ == "__main__":
    unittest.main()
