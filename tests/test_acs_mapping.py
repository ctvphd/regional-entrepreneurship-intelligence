"""Tests for ACS geography mapping audits."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.reference import (
    load_authoritative_reference_data,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_acs import load_acs_raw
from regional_entrepreneurship_intelligence.etl.transform_acs import (
    audit_acs_geography,
    classify_geography_code,
)


class ACSMappingAuditTest(unittest.TestCase):
    def test_acs_geography_audit_classifies_direct_and_unresolved_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "acs_mapping.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            try:
                create_schema(connection)
                load_authoritative_reference_data(connection)
                load_acs_raw(connection)

                geography = audit_acs_geography(connection)

                self.assertEqual(geography.unique_codes, 3)
                self.assertEqual(geography.status_counts, {"direct_match": 3})
                self.assertEqual(geography.row_counts["direct_match"], 60)
                self.assertEqual(classify_geography_code(connection, "10180"), "direct_match")
                self.assertEqual(classify_geography_code(connection, "99999"), "unresolved")
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
