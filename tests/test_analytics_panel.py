"""Tests for the integrated metropolitan analytical panel."""

from __future__ import annotations

import sqlite3
import unittest

from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.build_analytics_panel import build_panel


class AnalyticsPanelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute("PRAGMA foreign_keys=ON")
        create_schema(self.connection)
        self.connection.executemany(
            "INSERT INTO ref_geography (geography_id,cbsa_code,cbsa_name,geography_type,source_vintage) VALUES (?,?,?,?,?)",
            [(1, "10180", "Metro A", "MSA", "2023"), (2, "99999", "Micro B", "MICROPOLITAN", "2023")],
        )
        self.connection.execute(
            "INSERT INTO ref_industry (industry_id,naics_code,naics_level,naics_title,naics_version) VALUES (1,'11',2,'Agriculture','2022')"
        )
        self.connection.executemany(
            "INSERT INTO int_entrepreneurship (geography_id,industry_id,year,firm_startups,startup_rate,startup_rate_lag1,establishment_entry_rate) VALUES (?,?,?,?,?,?,?)",
            [(1, 1, 2020, 10, 2.5, 2.0, 1.1), (1, 1, 2021, 11, 2.6, 2.5, 1.2), (1, 1, 2022, 12, 2.7, 2.6, 1.3), (2, 1, 2020, 3, 2.4, None, None)],
        )
        self.connection.executemany(
            "INSERT INTO int_industry_growth (geography_id,industry_id,year,employment,establishments,payroll,average_wage,employment_growth,is_complete_county_coverage) VALUES (1,1,?,?,?,?,?,?,1)",
            [(2020, 1000, 100, 5000, 50000, 0.1), (2021, 1100, 105, 5500, 51000, 0.11), (2023, 1200, 110, 6000, 52000, 0.12)],
        )
        self.connection.execute(
            "INSERT INTO int_regional_controls (geography_id,year,population,median_household_income,educational_attainment_pct,labor_force_participation_pct,unemployment_rate) VALUES (1,2020,100000,60000,30,65,4)"
        )
        self.connection.execute(
            "INSERT INTO int_business_structure (geography_id,industry_id,year,establishments,employment,annual_payroll,first_quarter_payroll,is_complete_county_coverage) VALUES (1,1,2020,99,980,4900,1200,1)"
        )
        self.connection.commit()

    def tearDown(self) -> None:
        self.connection.close()

    def test_panel_preserves_core_and_left_join_missing_support(self) -> None:
        first = build_panel(self.connection)
        self.assertEqual(first["merge_audit"]["bds_qcew_matched"], 2)
        self.assertEqual(first["merge_audit"]["bds_only"], 1)
        self.assertEqual(first["merge_audit"]["qcew_only"], 1)
        self.assertEqual(first["merge_audit"]["acs_matched"], 1)
        self.assertEqual(first["merge_audit"]["acs_unmatched"], 1)
        self.assertEqual(first["merge_audit"]["cbp_matched"], 1)
        self.assertEqual(first["merge_audit"]["cbp_unmatched"], 1)
        self.assertEqual(first["panel"]["final_rows"], 2)
        row = self.connection.execute(
            "SELECT startup_rate,qcew_employment,acs_population,cbp_employment,cbp_annual_payroll,acs_matched,cbp_matched FROM analytics_msa_industry_year WHERE year=2020"
        ).fetchone()
        self.assertEqual(tuple(row), (2.5, 1000, 100000, 980, 4900, 1, 1))
        self.assertEqual(first["geography"]["micropolitan_bds_intermediate_rows_excluded"], 1)

    def test_missing_acs_and_cbp_do_not_drop_core_row_or_multiply(self) -> None:
        self.connection.execute("DELETE FROM int_regional_controls")
        self.connection.execute("UPDATE int_business_structure SET year=2022")
        self.connection.execute(
            "INSERT INTO stg_cbp (geography_id,industry_id,year,is_suppressed) VALUES (1,1,2021,1)"
        )
        self.connection.commit()
        result = build_panel(self.connection)
        self.assertEqual(result["panel"]["final_rows"], 2)
        self.assertEqual(result["merge_audit"]["acs_unmatched"], 2)
        self.assertEqual(result["merge_audit"]["cbp_unmatched"], 2)
        self.assertEqual(result["panel"]["duplicate_keys"], 0)
        self.assertEqual(result["panel"]["quality_flags"]["cbp_has_suppression"], 1)
        self.assertEqual(result["panel"]["quality_flags"]["cbp_incomplete_county_coverage"], 1)
        self.assertEqual(tuple(self.connection.execute("SELECT acs_matched,cbp_matched FROM analytics_msa_industry_year").fetchone()), (0, 0))

    def test_rebuild_is_idempotent_and_has_no_leakage_columns(self) -> None:
        first = build_panel(self.connection)
        first_metrics = self.connection.execute(
            "SELECT metric_name,metric_value FROM quality_table_metric WHERE pipeline_run_id=? ORDER BY metric_name",
            (first["pipeline_run_id"],),
        ).fetchall()
        second = build_panel(self.connection)
        second_metrics = self.connection.execute(
            "SELECT metric_name,metric_value FROM quality_table_metric WHERE pipeline_run_id=? ORDER BY metric_name",
            (second["pipeline_run_id"],),
        ).fetchall()
        self.assertNotEqual(first["pipeline_run_id"], second["pipeline_run_id"])
        self.assertEqual(first["panel"]["final_rows"], second["panel"]["final_rows"])
        self.assertEqual(first["merge_audit"], second["merge_audit"])
        self.assertEqual(first_metrics, second_metrics)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM analytics_msa_industry_year").fetchone()[0], 2)
        names = {row[1].lower() for row in self.connection.execute("PRAGMA table_info(analytics_msa_industry_year)")}
        forbidden = {"expected_entrepreneurship", "alignment_residual", "entrepreneurial_gap", "startup_rate_lead1", "startup_rate_lead3"}
        self.assertFalse(names & forbidden)
        self.assertIn("qcew_employment", names)
        self.assertIn("cbp_employment", names)

    def test_duplicate_acs_keys_stop_before_rebuild(self) -> None:
        build_panel(self.connection)
        self.connection.execute("DROP TABLE int_regional_controls")
        self.connection.execute("CREATE TABLE int_regional_controls (geography_id INTEGER, year INTEGER)")
        self.connection.executemany("INSERT INTO int_regional_controls VALUES (1,2020)", [(), ()])
        self.connection.commit()
        with self.assertRaisesRegex(ValueError, "Source intermediate key duplicates"):
            build_panel(self.connection)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM analytics_msa_industry_year").fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
