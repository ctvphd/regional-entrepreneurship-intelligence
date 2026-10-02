"""Tests for QCEW geography, industry, and ownership mapping decisions."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from regional_entrepreneurship_intelligence.database.reference import (
    load_authoritative_reference_data,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_qcew import load_qcew_raw
from regional_entrepreneurship_intelligence.etl.transform_qcew import (
    PRIVATE_OWNERSHIP_CODE,
    audit_qcew_geography,
    audit_qcew_industry,
    classify_geography_code,
    classify_industry_code,
)


class QCEWMappingAuditTest(unittest.TestCase):
    def test_qcew_mapping_audits_county_crosswalk_and_sector_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            connection = sqlite3.connect(Path(tmpdir) / "qcew_mapping.sqlite")
            connection.execute("PRAGMA foreign_keys = ON;")
            try:
                create_schema(connection)
                load_authoritative_reference_data(connection)
                load_qcew_raw(connection)

                geography = audit_qcew_geography(connection)
                industry = audit_qcew_industry(connection)

                self.assertEqual(geography.status_counts, {"crosswalk_required": 3})
                self.assertEqual(geography.row_counts["crosswalk_required"], 36)
                self.assertEqual(
                    classify_geography_code(connection, "48059"),
                    "crosswalk_required",
                )
                self.assertEqual(classify_geography_code(connection, "99999"), "unresolved")

                self.assertEqual(industry.status_counts["directly_comparable"], 4)
                self.assertEqual(industry.status_counts["unresolved"], 6)
                self.assertEqual(
                    classify_industry_code(connection, "31-33"),
                    "directly_comparable",
                )
                self.assertEqual(classify_industry_code(connection, "10"), "unresolved")

                excluded_ownership_rows = connection.execute(
                    "SELECT COUNT(*) FROM raw_qcew WHERE source_ownership_code <> ?;",
                    (PRIVATE_OWNERSHIP_CODE,),
                ).fetchone()[0]
                self.assertEqual(excluded_ownership_rows, 6)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
