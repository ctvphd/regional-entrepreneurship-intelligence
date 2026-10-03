"""Lightweight contracts for the Assignment 5 EDA foundation."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from regional_entrepreneurship_intelligence.analysis.eda import (
    ANALYTICAL_VIEW,
    PANEL_KEYS,
    REQUIRED_EDA_FIELDS,
    STUDY_YEARS,
    VARIABLE_GROUPS,
    load_analytical_panel,
    validate_eda_schema,
)


class EDAFoundationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "eda.sqlite"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _create_database(
        self, *, add_target: bool = False, starting_year: int = 2010, geography_type: str = "MSA"
    ) -> None:
        columns = set().union(*VARIABLE_GROUPS.values()) | set(REQUIRED_EDA_FIELDS)
        if add_target:
            columns.add("future_target")
        con = sqlite3.connect(self.database)
        try:
            con.execute("CREATE TABLE ref_geography (geography_id INTEGER, geography_type TEXT)")
            con.execute("INSERT INTO ref_geography VALUES (1, ?)", (geography_type,))
            con.execute(
                "CREATE TABLE analytics_msa_industry_year "
                "(geography_id INTEGER, industry_id INTEGER, year INTEGER)"
            )
            definitions = ", ".join(
                f'"{name}" {"INTEGER" if name in PANEL_KEYS else "TEXT"}'
                for name in sorted(columns)
            )
            con.execute(f"CREATE TABLE eda_rows ({definitions})")
            names = sorted(columns)
            quoted_names = ", ".join('"' + name + '"' for name in names)
            placeholders = ", ".join("?" for _ in names)
            for year in (starting_year, 2023):
                values = {name: "x" for name in names}
                values.update({"geography_id": 1, "industry_id": 1, "year": year})
                con.execute(
                    f"INSERT INTO eda_rows ({quoted_names}) VALUES ({placeholders})",
                    [values[name] for name in names],
                )
                con.execute(
                    "INSERT INTO analytics_msa_industry_year VALUES (1, 1, ?)", (year,)
                )
            con.execute(f"CREATE VIEW {ANALYTICAL_VIEW} AS SELECT * FROM eda_rows")
            con.commit()
        finally:
            con.close()

    def test_loader_reads_panel_and_checks_study_year_and_msa_scope(self) -> None:
        self._create_database()
        frame = load_analytical_panel(self.database)
        self.assertEqual(len(frame), 2)
        self.assertEqual(tuple(PANEL_KEYS), ("geography_id", "industry_id", "year"))
        self.assertEqual(STUDY_YEARS, (2010, 2023))

    def test_variable_groups_reference_existing_fields(self) -> None:
        self._create_database()
        with closing(sqlite3.connect(self.database)) as con:
            columns = validate_eda_schema(con)
        self.assertTrue(REQUIRED_EDA_FIELDS.issubset(columns))
        self.assertTrue(set().union(*VARIABLE_GROUPS.values()).issubset(columns))

    def test_loader_rejects_target_fields(self) -> None:
        self._create_database(add_target=True)
        with self.assertRaisesRegex(ValueError, "Potential target or leakage"):
            load_analytical_panel(self.database)

    def test_loader_rejects_out_of_window_year(self) -> None:
        self._create_database(starting_year=2009)
        with self.assertRaisesRegex(ValueError, "Unexpected analytical year range"):
            load_analytical_panel(self.database)

    def test_loader_rejects_non_metropolitan_scope(self) -> None:
        self._create_database(geography_type="MicroSA")
        with self.assertRaisesRegex(ValueError, "Non-metropolitan rows"):
            load_analytical_panel(self.database)


if __name__ == "__main__":
    unittest.main()
