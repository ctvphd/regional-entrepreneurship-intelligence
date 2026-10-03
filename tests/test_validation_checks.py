"""Focused tests for reusable validation functions."""

import sqlite3
import unittest

from regional_entrepreneurship_intelligence.validation.checks import (
    validate_no_leakage_columns,
    validate_nonnegative,
    validate_percentage_bounds,
    validate_required_columns,
    validate_unique_key,
    validate_year_range,
)


class ValidationChecksTest(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute("CREATE TABLE panel (geo INTEGER, industry INTEGER, year INTEGER, rate REAL, count REAL)")
        self.connection.executemany(
            "INSERT INTO panel VALUES (?, ?, ?, ?, ?)",
            [(1, 11, 2010, 4.2, 10), (1, 11, 2011, 5.0, 12)],
        )

    def tearDown(self):
        self.connection.close()

    def test_valid_key_years_and_absent_leakage_pass(self):
        self.assertEqual(validate_unique_key(self.connection, "panel", ("geo", "industry", "year")), 0)
        validate_year_range(self.connection, "panel", "year", 2010, 2023)
        validate_percentage_bounds(self.connection, "panel", ("rate",))
        validate_nonnegative(self.connection, "panel", ("count",))
        validate_no_leakage_columns(self.connection, "panel", ("expected_entrepreneurship",))

    def test_duplicate_key_and_invalid_values_fail_explicitly(self):
        self.connection.execute("INSERT INTO panel VALUES (1, 11, 2010, 3.0, 2)")
        with self.assertRaisesRegex(ValueError, "duplicate groups"):
            validate_unique_key(self.connection, "panel", ("geo", "industry", "year"))
        with self.assertRaisesRegex(ValueError, "missing required columns"):
            validate_required_columns(self.connection, "panel", ("not_a_column",))

    def test_range_and_leakage_violations_fail(self):
        self.connection.execute("UPDATE panel SET rate=105 WHERE year=2010")
        with self.assertRaisesRegex(ValueError, "outside \\[0, 100\\]"):
            validate_percentage_bounds(self.connection, "panel", ("rate",))
        self.connection.execute("UPDATE panel SET year=2024 WHERE year=2011")
        with self.assertRaisesRegex(ValueError, "outside 2010-2023"):
            validate_year_range(self.connection, "panel", "year", 2010, 2023)
        self.connection.execute("ALTER TABLE panel ADD COLUMN model_prediction REAL")
        with self.assertRaisesRegex(ValueError, "prohibited leakage"):
            validate_no_leakage_columns(self.connection, "panel", ("model_prediction",))


if __name__ == "__main__":
    unittest.main()
