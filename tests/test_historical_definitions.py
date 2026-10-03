"""Focused historical-source and production-scope guards for A4.11B."""

import unittest
import sqlite3
from unittest.mock import patch

from regional_entrepreneurship_intelligence.database.naics_versions import (
    classify_sector, source_year_naics,
)
from regional_entrepreneurship_intelligence.database.reference import load_authoritative_reference_data
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.acs_variable_registry import (
    ids_for, load_registry, validate_label,
)
from regional_entrepreneurship_intelligence.etl.audit_bds_production import missing_reason
from regional_entrepreneurship_intelligence.etl.extract_qcew import row_has_status


class HistoricalDefinitionsTests(unittest.TestCase):
    def test_source_year_vintages(self):
        self.assertEqual(source_year_naics("QCEW", 2010).native_version, "2007")
        self.assertEqual(source_year_naics("QCEW", 2022).native_version, "2022")
        self.assertEqual(source_year_naics("CBP", 2011).native_version, "2007")
        self.assertEqual(source_year_naics("CBP", 2023).native_version, "2017")
        self.assertEqual(source_year_naics("BDS", 2010).native_version, "2017")

    def test_official_sector_chain(self):
        for version in ("2007", "2012", "2017"):
            for sector in ("11", "31-33", "44-45", "48-49", "72"):
                self.assertEqual(classify_sector(version, sector), ("directly_comparable", sector))
        self.assertEqual(classify_sector("2007", "99"), ("unresolved", None))

    def test_ambiguous_sector_concordance_stays_unresolved(self):
        with patch(
            "regional_entrepreneurship_intelligence.database.naics_versions._sector_relations",
            return_value={"11": {"11", "21"}},
        ):
            self.assertEqual(classify_sector("2007", "11"), ("unresolved", None))
        with patch(
            "regional_entrepreneurship_intelligence.database.naics_versions._sector_relations",
            return_value={"11": {"11"}, "21": {"11"}},
        ):
            self.assertEqual(classify_sector("2007", "11"), ("unresolved", None))

    def test_acs_education_shift_and_metadata(self):
        registry = load_registry()
        self.assertEqual(ids_for("educational_attainment_pct", 2018)[0], "DP02_0067PE")
        self.assertEqual(ids_for("educational_attainment_pct", 2019)[0], "DP02_0068PE")
        self.assertEqual(len(registry), 70)
        self.assertEqual(registry[(2019, "educational_attainment_pct")]["universe"], "Population 25 years and over")
        with self.assertRaises(ValueError):
            validate_label("educational_attainment_pct", "Percent veterans")

    def test_bds_missingness_reasons(self):
        self.assertEqual(missing_reason("D", "10", "direct_match", "directly_comparable"), "numerator_suppressed")
        self.assertEqual(missing_reason("2", "S", "direct_match", "directly_comparable"), "denominator_suppressed")
        self.assertEqual(missing_reason("0", "0", "direct_match", "directly_comparable"), "denominator_zero")
        self.assertEqual(missing_reason("2", "", "direct_match", "directly_comparable"), "denominator_missing")
        self.assertEqual(missing_reason("D", "0", "unresolved", "directly_comparable"), "geography_mismatch")

    def test_bds_primary_scope_is_metropolitan_only(self):
        with sqlite3.connect(":memory:") as connection:
            create_schema(connection)
            load_authoritative_reference_data(connection)
            industry_id = connection.execute(
                "SELECT industry_id FROM ref_industry WHERE naics_code = '11' AND naics_version = '2022'"
            ).fetchone()[0]
            for kind in ("MSA", "MICROPOLITAN"):
                geography_id = connection.execute(
                    "SELECT geography_id FROM ref_geography WHERE geography_type = ? LIMIT 1", (kind,)
                ).fetchone()[0]
                connection.execute(
                    "INSERT INTO int_entrepreneurship (geography_id, industry_id, year) VALUES (?, ?, 2010)",
                    (geography_id, industry_id),
                )
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM int_entrepreneurship"
            ).fetchone()[0], 2)
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM v_bds_metropolitan_eligible"
            ).fetchone()[0], 1)

    def test_qcew_lq_and_oty_flags_do_not_suppress_annual_values(self):
        self.assertFalse(row_has_status({
            "disclosure_code": "", "lq_disclosure_code": "N", "oty_disclosure_code": "N"
        }))
        self.assertTrue(row_has_status({"disclosure_code": "N"}))


if __name__ == "__main__":
    unittest.main()
