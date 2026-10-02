"""Tests for BDS geography and industry mapping audits."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.reference import (
    load_authoritative_reference_data,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_bds import (
    load_bds_firm_age_raw,
    load_bds_raw,
)
from regional_entrepreneurship_intelligence.etl.transform_bds import (
    audit_bds_geography,
    audit_bds_industry,
    classify_geography_code,
    classify_industry_code,
)


class BDSMappingAuditTest(unittest.TestCase):
    def test_bds_mapping_audits_classify_direct_and_unresolved_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "bds_mapping.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            create_schema(connection)
            load_authoritative_reference_data(connection)
            load_bds_raw(connection)
            load_bds_firm_age_raw(connection)

            geography = audit_bds_geography(connection)
            industry = audit_bds_industry(connection)

            self.assertEqual(geography.unique_codes, 2)
            self.assertEqual(geography.status_counts, {"direct_match": 2})
            self.assertEqual(industry.unique_codes, 4)
            self.assertEqual(industry.status_counts, {"directly_comparable": 4})
            self.assertEqual(classify_geography_code(connection, "99999"), "unresolved")
            self.assertEqual(classify_industry_code(connection, "99"), "unresolved")
            self.assertEqual(
                classify_industry_code(connection, "31-33"),
                "directly_comparable",
            )

            connection.close()


if __name__ == "__main__":
    unittest.main()
