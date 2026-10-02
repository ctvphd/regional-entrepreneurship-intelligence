"""Tests for CBP geography and industry mapping audits."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.reference import (
    load_authoritative_reference_data,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_cbp import load_cbp_raw
from regional_entrepreneurship_intelligence.etl.transform_cbp import (
    audit_cbp_geography,
    audit_cbp_industry,
    classify_geography_code,
    classify_industry_code,
)


class CBPMappingTest(unittest.TestCase):
    def test_cbp_mapping_audits_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "cbp_mapping.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            try:
                create_schema(connection)
                load_authoritative_reference_data(connection)
                load_cbp_raw(connection)

                geography = audit_cbp_geography(connection)
                industry = audit_cbp_industry(connection)

                self.assertEqual(geography.unique_codes, 3)
                self.assertEqual(geography.status_counts, {"crosswalk_required": 3})
                self.assertEqual(geography.row_counts, {"crosswalk_required": 26})
                self.assertEqual(classify_geography_code(connection, "48059"), "crosswalk_required")
                self.assertEqual(classify_geography_code(connection, "99999"), "unresolved")

                self.assertEqual(industry.unique_codes, 5)
                self.assertEqual(
                    industry.status_counts,
                    {"unresolved": 1, "directly_comparable": 4},
                )
                self.assertEqual(industry.row_counts["unresolved"], 6)
                self.assertEqual(industry.row_counts["directly_comparable"], 20)
                self.assertEqual(classify_industry_code(connection, "31-33"), "directly_comparable")
                self.assertEqual(classify_industry_code(connection, "00"), "unresolved")
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
