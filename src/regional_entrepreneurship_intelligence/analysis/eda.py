"""Read-only foundations and variable groups for Assignment 5 EDA."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EDA_DATABASE = PROJECT_ROOT / "database" / "assignment4_production.sqlite"
ANALYTICAL_VIEW = "v_analytics_msa_industry_year"
STUDY_YEARS = (2010, 2023)
PANEL_KEYS = ("geography_id", "industry_id", "year")
REQUIRED_EDA_FIELDS = frozenset(
    {
        *PANEL_KEYS,
        "cbsa_code",
        "sector_code",
        "startup_rate",
        "employment_growth",
        "acs_population_growth",
        "median_household_income",
        "educational_attainment_pct",
        "labor_force_participation_pct",
        "unemployment_rate",
    }
)
FORBIDDEN_FIELD_FRAGMENTS = (
    "target",
    "label",
    "prediction",
    "expected_entrepreneurship",
    "alignment",
    "entrepreneurial_gap",
    "future_",
    "lead_",
)

VARIABLE_GROUPS: dict[str, frozenset[str]] = {
    "identifier": frozenset(
        {"geography_id", "industry_id", "year", "cbsa_code", "cbsa_name", "sector_code", "sector_title"}
    ),
    "entrepreneurship": frozenset(
        {
            "startup_rate",
            "firm_startups",
            "startup_rate_lag1",
            "startup_rate_lag2",
            "startup_rate_lag3",
            "establishment_entry",
            "establishment_entry_rate",
            "startup_job_creation",
        }
    ),
    "industry_growth": frozenset(
        {
            "qcew_employment",
            "qcew_establishments",
            "qcew_payroll",
            "qcew_average_wage",
            "qcew_total_annual_wages_nominal",
            "qcew_average_annual_pay_nominal",
            "employment_growth",
            "establishment_growth",
            "payroll_growth",
            "wage_growth",
            "employment_growth_lag1",
            "employment_growth_lag2",
            "employment_growth_lag3",
            "establishment_growth_lag1",
            "establishment_growth_lag2",
            "establishment_growth_lag3",
            "payroll_growth_lag1",
            "average_pay_growth_lag1",
        }
    ),
    "regional_control": frozenset(
        {
            "acs_population",
            "acs_population_growth",
            "acs_population_growth_lag1",
            "median_household_income",
            "median_household_income_lag1",
            "educational_attainment_pct",
            "educational_attainment_pct_lag1",
            "labor_force_participation_pct",
            "labor_force_participation_pct_lag1",
            "unemployment_rate",
            "unemployment_rate_lag1",
        }
    ),
    "business_structure": frozenset(
        {"cbp_establishments", "cbp_employment", "cbp_annual_payroll", "cbp_first_quarter_payroll"}
    ),
    "quality_flag": frozenset(
        {
            "bds_has_suppression",
            "bds_startup_available",
            "qcew_has_suppression",
            "qcew_is_complete_county_coverage",
            "qcew_is_real_adjusted",
            "acs_matched",
            "acs_has_suppression",
            "acs_has_missing_controls",
            "cbp_matched",
            "cbp_has_suppression",
            "cbp_is_complete_county_coverage",
            "has_suppression",
        }
    ),
    "metadata_supporting": frozenset({"source_quality_notes"}),
}


def _connect_read_only(database_path: str | Path) -> sqlite3.Connection:
    path = Path(database_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"EDA database does not exist: {path}")
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def validate_eda_schema(connection: sqlite3.Connection) -> set[str]:
    """Check the active analytical view for required fields and leakage names."""
    objects = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
        )
    }
    if ANALYTICAL_VIEW not in objects:
        raise ValueError(f"Required analytical view is missing: {ANALYTICAL_VIEW}")
    columns = {
        row[1] for row in connection.execute(f"PRAGMA table_info({ANALYTICAL_VIEW})")
    }
    missing = REQUIRED_EDA_FIELDS - columns
    if missing:
        raise ValueError(f"Required EDA fields are missing: {sorted(missing)}")
    forbidden = sorted(
        name
        for name in columns
        if any(fragment in name.lower() for fragment in FORBIDDEN_FIELD_FRAGMENTS)
    )
    if forbidden:
        raise ValueError(f"Potential target or leakage fields found: {forbidden}")
    grouped = set().union(*VARIABLE_GROUPS.values())
    invalid = sorted(grouped - columns)
    if invalid:
        raise ValueError(f"EDA variable groups reference absent fields: {invalid}")
    return columns


def load_analytical_panel(
    database_path: str | Path = DEFAULT_EDA_DATABASE,
    *,
    validate: bool = True,
) -> pd.DataFrame:
    """Load the active Assignment 4 panel from SQLite without writing to it."""
    with closing(_connect_read_only(database_path)) as connection:
        columns = validate_eda_schema(connection) if validate else None
        frame = pd.read_sql_query(f"SELECT * FROM {ANALYTICAL_VIEW}", connection)
        if validate:
            assert columns is not None
            if frame.empty:
                raise ValueError("The analytical panel is empty")
            if frame["year"].min() != STUDY_YEARS[0] or frame["year"].max() != STUDY_YEARS[1]:
                raise ValueError(f"Unexpected analytical year range: {frame['year'].min()}-{frame['year'].max()}")
            if frame.duplicated(list(PANEL_KEYS)).any():
                raise ValueError("Duplicate analytical panel keys found")
            non_msa = connection.execute(
                """SELECT COUNT(*) FROM analytics_msa_industry_year AS a
                   JOIN ref_geography AS g USING (geography_id)
                   WHERE g.geography_type IS NOT 'MSA'"""
            ).fetchone()[0]
            if non_msa:
                raise ValueError(f"Non-metropolitan rows found in analytical panel: {non_msa}")
        return frame
