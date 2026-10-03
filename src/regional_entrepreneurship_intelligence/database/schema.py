"""Create the Assignment 4 SQLite schema.

This module defines the planned normalized schema for Assignment 4.2. It creates
empty tables, constraints, and indexes only; it does not extract, download, or
load live source data.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from regional_entrepreneurship_intelligence.database.connection import (
    DEFAULT_DATABASE_PATH,
    connect_database,
)


SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS ref_geography (
        geography_id INTEGER PRIMARY KEY,
        cbsa_code TEXT NOT NULL,
        cbsa_name TEXT NOT NULL,
        geography_type TEXT NOT NULL CHECK (geography_type IN ('MSA', 'MICROPOLITAN', 'COUNTY', 'STATE', 'NATIONAL', 'OTHER')),
        state_codes TEXT,
        valid_from_year INTEGER CHECK (valid_from_year IS NULL OR valid_from_year BETWEEN 1900 AND 2100),
        valid_to_year INTEGER CHECK (valid_to_year IS NULL OR valid_to_year BETWEEN 1900 AND 2100),
        source_vintage TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
        notes TEXT,
        UNIQUE (cbsa_code, source_vintage)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ref_industry (
        industry_id INTEGER PRIMARY KEY,
        naics_code TEXT NOT NULL,
        naics_level INTEGER NOT NULL CHECK (naics_level BETWEEN 2 AND 6),
        naics_title TEXT NOT NULL,
        naics_version TEXT NOT NULL,
        parent_naics_code TEXT,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
        notes TEXT,
        UNIQUE (naics_code, naics_version)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ref_year (
        year INTEGER PRIMARY KEY CHECK (year BETWEEN 1900 AND 2100),
        is_primary_study_year INTEGER NOT NULL DEFAULT 0 CHECK (is_primary_study_year IN (0, 1)),
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ref_source (
        source_id INTEGER PRIMARY KEY,
        source_name TEXT NOT NULL UNIQUE,
        source_agency TEXT,
        dataset_name TEXT,
        default_access_method TEXT,
        homepage_url TEXT,
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ref_geography_county_crosswalk (
        county_crosswalk_id INTEGER PRIMARY KEY,
        geography_id INTEGER NOT NULL REFERENCES ref_geography(geography_id),
        cbsa_code TEXT NOT NULL,
        county_name TEXT NOT NULL,
        state_name TEXT NOT NULL,
        state_fips TEXT NOT NULL CHECK (length(state_fips) = 2),
        county_fips TEXT NOT NULL CHECK (length(county_fips) = 3),
        county_geoid TEXT NOT NULL CHECK (length(county_geoid) = 5),
        central_outlying TEXT CHECK (central_outlying IS NULL OR central_outlying IN ('Central', 'Outlying')),
        source_vintage TEXT NOT NULL,
        notes TEXT,
        UNIQUE (cbsa_code, county_geoid, source_vintage)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS metadata_source_manifest (
        manifest_id INTEGER PRIMARY KEY,
        source_id INTEGER REFERENCES ref_source(source_id),
        source_name TEXT NOT NULL,
        source_agency TEXT,
        dataset_name TEXT,
        access_method TEXT,
        source_url_or_endpoint TEXT,
        retrieval_timestamp TEXT,
        source_year INTEGER CHECK (source_year IS NULL OR source_year BETWEEN 1900 AND 2100),
        source_version TEXT,
        raw_filename TEXT,
        file_checksum TEXT,
        row_count INTEGER CHECK (row_count IS NULL OR row_count >= 0),
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS metadata_pipeline_run (
        pipeline_run_id TEXT PRIMARY KEY,
        start_timestamp TEXT NOT NULL,
        end_timestamp TEXT,
        status TEXT NOT NULL CHECK (status IN ('planned', 'running', 'success', 'failed', 'partial')),
        stage TEXT NOT NULL,
        records_read INTEGER DEFAULT 0 CHECK (records_read >= 0),
        records_written INTEGER DEFAULT 0 CHECK (records_written >= 0),
        records_rejected INTEGER DEFAULT 0 CHECK (records_rejected >= 0),
        warnings TEXT,
        error_message TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS raw_bds (
        raw_bds_id INTEGER PRIMARY KEY,
        manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        source_year INTEGER CHECK (source_year IS NULL OR source_year BETWEEN 1900 AND 2100),
        source_geography_id TEXT,
        source_industry_id TEXT,
        source_naics_version TEXT,
        source_row_identifier TEXT,
        raw_source_filename TEXT,
        is_suppressed INTEGER CHECK (is_suppressed IS NULL OR is_suppressed IN (0, 1)),
        raw_payload TEXT,
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS raw_bds_firm_age (
        raw_bds_firm_age_id INTEGER PRIMARY KEY,
        manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        source_year INTEGER CHECK (source_year IS NULL OR source_year BETWEEN 1900 AND 2100),
        source_geography_id TEXT,
        source_industry_id TEXT,
        source_fagecoarse TEXT,
        source_naics_version TEXT,
        source_row_identifier TEXT,
        raw_source_filename TEXT,
        is_suppressed INTEGER CHECK (is_suppressed IS NULL OR is_suppressed IN (0, 1)),
        raw_payload TEXT,
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS raw_qcew (
        raw_qcew_id INTEGER PRIMARY KEY,
        manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        source_year INTEGER CHECK (source_year IS NULL OR source_year BETWEEN 1900 AND 2100),
        source_geography_id TEXT,
        source_industry_id TEXT,
        source_ownership_code TEXT,
        source_size_code TEXT,
        source_naics_version TEXT,
        source_row_identifier TEXT,
        raw_source_filename TEXT,
        disclosure_code TEXT,
        annual_avg_estabs TEXT,
        annual_avg_emplvl TEXT,
        total_annual_wages TEXT,
        avg_annual_pay TEXT,
        is_suppressed INTEGER CHECK (is_suppressed IS NULL OR is_suppressed IN (0, 1)),
        raw_payload TEXT,
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS raw_cbp (
        raw_cbp_id INTEGER PRIMARY KEY,
        manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        source_year INTEGER CHECK (source_year IS NULL OR source_year BETWEEN 1900 AND 2100),
        source_geography_id TEXT,
        source_state_fips TEXT,
        source_county_fips TEXT,
        source_county_geoid TEXT,
        source_industry_id TEXT,
        source_industry_label TEXT,
        source_naics_version TEXT,
        legal_form_code TEXT,
        employment_size_code TEXT,
        source_row_identifier TEXT,
        raw_source_filename TEXT,
        establishments TEXT,
        establishments_flag TEXT,
        employment TEXT,
        employment_flag TEXT,
        annual_payroll TEXT,
        annual_payroll_flag TEXT,
        first_quarter_payroll TEXT,
        first_quarter_payroll_flag TEXT,
        is_suppressed INTEGER CHECK (is_suppressed IS NULL OR is_suppressed IN (0, 1)),
        raw_payload TEXT,
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS raw_acs (
        raw_acs_id INTEGER PRIMARY KEY,
        manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        source_year INTEGER CHECK (source_year IS NULL OR source_year BETWEEN 1900 AND 2100),
        source_geography_id TEXT,
        source_geography_name TEXT,
        source_industry_id TEXT,
        source_variable_id TEXT,
        source_moe_variable_id TEXT,
        source_product TEXT,
        control_name TEXT,
        estimate_value TEXT,
        margin_of_error TEXT,
        source_naics_version TEXT,
        source_row_identifier TEXT,
        raw_source_filename TEXT,
        is_suppressed INTEGER CHECK (is_suppressed IS NULL OR is_suppressed IN (0, 1)),
        raw_payload TEXT,
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS stg_bds (
        stg_bds_id INTEGER PRIMARY KEY,
        raw_bds_id INTEGER REFERENCES raw_bds(raw_bds_id),
        manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        geography_id INTEGER REFERENCES ref_geography(geography_id),
        industry_id INTEGER REFERENCES ref_industry(industry_id),
        year INTEGER REFERENCES ref_year(year),
        source_geography_id TEXT,
        source_industry_id TEXT,
        source_fagecoarse TEXT,
        standardized_cbsa_code TEXT,
        standardized_cbsa_name TEXT,
        standardized_sector_code TEXT,
        geography_mapping_status TEXT CHECK (geography_mapping_status IS NULL OR geography_mapping_status IN ('direct_match', 'crosswalk_required', 'unresolved')),
        industry_mapping_status TEXT CHECK (industry_mapping_status IS NULL OR industry_mapping_status IN ('directly_comparable', 'official_mapping_required', 'unresolved')),
        firm_startups REAL,
        startup_rate REAL,
        establishment_entry REAL,
        establishment_entry_rate REAL,
        startup_job_creation REAL,
        is_missing INTEGER CHECK (is_missing IS NULL OR is_missing IN (0, 1)),
        is_suppressed INTEGER CHECK (is_suppressed IS NULL OR is_suppressed IN (0, 1)),
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS stg_qcew (
        stg_qcew_id INTEGER PRIMARY KEY,
        raw_qcew_id INTEGER REFERENCES raw_qcew(raw_qcew_id),
        manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        geography_id INTEGER REFERENCES ref_geography(geography_id),
        industry_id INTEGER REFERENCES ref_industry(industry_id),
        year INTEGER REFERENCES ref_year(year),
        source_geography_id TEXT,
        source_industry_id TEXT,
        source_ownership_code TEXT,
        ownership_scope TEXT,
        standardized_cbsa_code TEXT,
        standardized_cbsa_name TEXT,
        standardized_sector_code TEXT,
        geography_mapping_status TEXT CHECK (geography_mapping_status IS NULL OR geography_mapping_status IN ('direct_match', 'crosswalk_required', 'unresolved')),
        industry_mapping_status TEXT CHECK (industry_mapping_status IS NULL OR industry_mapping_status IN ('directly_comparable', 'official_mapping_required', 'unresolved')),
        employment REAL,
        establishments REAL,
        payroll REAL,
        average_pay REAL,
        total_annual_wages_nominal REAL,
        average_annual_pay_nominal REAL,
        counties_expected INTEGER CHECK (counties_expected IS NULL OR counties_expected >= 0),
        counties_observed INTEGER CHECK (counties_observed IS NULL OR counties_observed >= 0),
        counties_suppressed INTEGER CHECK (counties_suppressed IS NULL OR counties_suppressed >= 0),
        source_row_count INTEGER CHECK (source_row_count IS NULL OR source_row_count >= 0),
        is_complete_county_coverage INTEGER CHECK (is_complete_county_coverage IS NULL OR is_complete_county_coverage IN (0, 1)),
        is_missing INTEGER CHECK (is_missing IS NULL OR is_missing IN (0, 1)),
        is_suppressed INTEGER CHECK (is_suppressed IS NULL OR is_suppressed IN (0, 1)),
        source_raw_qcew_ids TEXT,
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS stg_cbp (
        stg_cbp_id INTEGER PRIMARY KEY,
        raw_cbp_id INTEGER REFERENCES raw_cbp(raw_cbp_id),
        manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        geography_id INTEGER REFERENCES ref_geography(geography_id),
        industry_id INTEGER REFERENCES ref_industry(industry_id),
        year INTEGER REFERENCES ref_year(year),
        source_state_fips TEXT,
        source_county_fips TEXT,
        source_county_geoid TEXT,
        source_county_name TEXT,
        source_industry_id TEXT,
        source_industry_label TEXT,
        source_naics_version TEXT,
        standardized_cbsa_code TEXT,
        standardized_cbsa_name TEXT,
        standardized_sector_code TEXT,
        geography_mapping_status TEXT CHECK (geography_mapping_status IS NULL OR geography_mapping_status IN ('direct_match', 'crosswalk_required', 'unresolved')),
        industry_mapping_status TEXT CHECK (industry_mapping_status IS NULL OR industry_mapping_status IN ('directly_comparable', 'official_mapping_required', 'unresolved')),
        establishments REAL,
        employment REAL,
        annual_payroll REAL,
        first_quarter_payroll REAL,
        is_missing INTEGER CHECK (is_missing IS NULL OR is_missing IN (0, 1)),
        is_suppressed INTEGER CHECK (is_suppressed IS NULL OR is_suppressed IN (0, 1)),
        noise_or_suppression_flags TEXT,
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS stg_acs (
        stg_acs_id INTEGER PRIMARY KEY,
        raw_acs_id INTEGER REFERENCES raw_acs(raw_acs_id),
        manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        geography_id INTEGER REFERENCES ref_geography(geography_id),
        year INTEGER REFERENCES ref_year(year),
        source_geography_id TEXT,
        source_geography_name TEXT,
        standardized_cbsa_code TEXT,
        standardized_cbsa_name TEXT,
        geography_mapping_status TEXT CHECK (geography_mapping_status IS NULL OR geography_mapping_status IN ('direct_match', 'crosswalk_required', 'unresolved')),
        population REAL,
        population_moe REAL,
        median_household_income REAL,
        median_household_income_moe REAL,
        educational_attainment_pct REAL,
        educational_attainment_pct_moe REAL,
        labor_force_participation_pct REAL,
        labor_force_participation_pct_moe REAL,
        unemployment_rate REAL,
        unemployment_rate_moe REAL,
        is_missing INTEGER CHECK (is_missing IS NULL OR is_missing IN (0, 1)),
        is_suppressed INTEGER CHECK (is_suppressed IS NULL OR is_suppressed IN (0, 1)),
        source_raw_acs_ids TEXT,
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS int_entrepreneurship (
        geography_id INTEGER NOT NULL REFERENCES ref_geography(geography_id),
        industry_id INTEGER NOT NULL REFERENCES ref_industry(industry_id),
        year INTEGER NOT NULL REFERENCES ref_year(year),
        firm_startups REAL,
        startup_rate REAL,
        establishment_entry REAL,
        establishment_entry_rate REAL,
        startup_job_creation REAL,
        startup_rate_lag1 REAL,
        startup_rate_lag2 REAL,
        startup_rate_lag3 REAL,
        lagged_startup_rate REAL,
        geography_mapping_status TEXT,
        industry_mapping_status TEXT,
        has_suppression INTEGER NOT NULL DEFAULT 0 CHECK (has_suppression IN (0, 1)),
        source_manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        notes TEXT,
        PRIMARY KEY (geography_id, industry_id, year)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS int_industry_growth (
        geography_id INTEGER NOT NULL REFERENCES ref_geography(geography_id),
        industry_id INTEGER NOT NULL REFERENCES ref_industry(industry_id),
        year INTEGER NOT NULL REFERENCES ref_year(year),
        standardized_cbsa_code TEXT,
        standardized_cbsa_name TEXT,
        standardized_sector_code TEXT,
        employment REAL,
        establishments REAL,
        payroll REAL,
        average_wage REAL,
        total_annual_wages_nominal REAL,
        average_annual_pay_nominal REAL,
        employment_growth REAL,
        establishment_growth REAL,
        payroll_growth REAL,
        wage_growth REAL,
        employment_growth_lag1 REAL,
        employment_growth_lag2 REAL,
        employment_growth_lag3 REAL,
        establishment_growth_lag1 REAL,
        establishment_growth_lag2 REAL,
        establishment_growth_lag3 REAL,
        payroll_growth_lag1 REAL,
        average_pay_growth_lag1 REAL,
        counties_expected INTEGER CHECK (counties_expected IS NULL OR counties_expected >= 0),
        counties_observed INTEGER CHECK (counties_observed IS NULL OR counties_observed >= 0),
        counties_suppressed INTEGER CHECK (counties_suppressed IS NULL OR counties_suppressed >= 0),
        is_complete_county_coverage INTEGER CHECK (is_complete_county_coverage IS NULL OR is_complete_county_coverage IN (0, 1)),
        geography_mapping_status TEXT,
        industry_mapping_status TEXT,
        is_real_adjusted INTEGER NOT NULL DEFAULT 0 CHECK (is_real_adjusted IN (0, 1)),
        has_suppression INTEGER NOT NULL DEFAULT 0 CHECK (has_suppression IN (0, 1)),
        source_manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        notes TEXT,
        PRIMARY KEY (geography_id, industry_id, year)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS int_regional_controls (
        geography_id INTEGER NOT NULL REFERENCES ref_geography(geography_id),
        year INTEGER NOT NULL REFERENCES ref_year(year),
        standardized_cbsa_code TEXT,
        standardized_cbsa_name TEXT,
        population REAL,
        population_growth REAL,
        median_household_income REAL,
        educational_attainment_pct REAL,
        labor_force_participation_pct REAL,
        unemployment_rate REAL,
        population_growth_lag1 REAL,
        median_household_income_lag1 REAL,
        educational_attainment_pct_lag1 REAL,
        labor_force_participation_pct_lag1 REAL,
        unemployment_rate_lag1 REAL,
        geography_mapping_status TEXT,
        has_suppression INTEGER NOT NULL DEFAULT 0 CHECK (has_suppression IN (0, 1)),
        source_manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        notes TEXT,
        PRIMARY KEY (geography_id, year)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS int_business_structure (
        geography_id INTEGER NOT NULL REFERENCES ref_geography(geography_id),
        industry_id INTEGER NOT NULL REFERENCES ref_industry(industry_id),
        year INTEGER NOT NULL REFERENCES ref_year(year),
        standardized_cbsa_code TEXT,
        standardized_cbsa_name TEXT,
        standardized_sector_code TEXT,
        establishments REAL,
        employment REAL,
        annual_payroll REAL,
        first_quarter_payroll REAL,
        counties_expected INTEGER CHECK (counties_expected IS NULL OR counties_expected >= 0),
        counties_observed INTEGER CHECK (counties_observed IS NULL OR counties_observed >= 0),
        counties_suppressed INTEGER CHECK (counties_suppressed IS NULL OR counties_suppressed >= 0),
        is_complete_county_coverage INTEGER CHECK (is_complete_county_coverage IS NULL OR is_complete_county_coverage IN (0, 1)),
        geography_mapping_status TEXT,
        industry_mapping_status TEXT,
        has_suppression INTEGER NOT NULL DEFAULT 0 CHECK (has_suppression IN (0, 1)),
        source_manifest_id INTEGER REFERENCES metadata_source_manifest(manifest_id),
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        notes TEXT,
        PRIMARY KEY (geography_id, industry_id, year)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS analytics_msa_industry_year (
        geography_id INTEGER NOT NULL REFERENCES ref_geography(geography_id),
        industry_id INTEGER NOT NULL REFERENCES ref_industry(industry_id),
        year INTEGER NOT NULL REFERENCES ref_year(year),
        startup_rate REAL,
        lagged_startup_rate REAL,
        employment REAL,
        establishments REAL,
        payroll REAL,
        average_wage REAL,
        employment_growth REAL,
        establishment_growth REAL,
        payroll_growth REAL,
        wage_growth REAL,
        population REAL,
        median_household_income REAL,
        educational_attainment_pct REAL,
        labor_force_participation_pct REAL,
        unemployment_rate REAL,
        business_structure_establishments REAL,
        business_structure_employment REAL,
        has_suppression INTEGER NOT NULL DEFAULT 0 CHECK (has_suppression IN (0, 1)),
        source_quality_notes TEXT,
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        PRIMARY KEY (geography_id, industry_id, year)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS quality_rejected_record (
        rejection_id INTEGER PRIMARY KEY,
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        source_id INTEGER REFERENCES ref_source(source_id),
        table_name TEXT NOT NULL,
        stage TEXT NOT NULL,
        source_row_identifier TEXT,
        reason_code TEXT NOT NULL CHECK (reason_code IN (
            'invalid_cbsa',
            'invalid_naics',
            'invalid_year',
            'duplicate_key',
            'missing_required_field',
            'invalid_numeric_value',
            'suppressed_value',
            'failed_reference_match',
            'unresolved_geography',
            'unresolved_industry',
            'excluded_ownership',
            'duplicate_standardized_key',
            'incomplete_aggregation',
            'missing_required_measure',
            'missing_required_startup_measure',
            'other'
        )),
        reason_detail TEXT,
        original_value TEXT,
        serialized_record TEXT,
        created_timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS quality_table_metric (
        metric_id INTEGER PRIMARY KEY,
        pipeline_run_id TEXT REFERENCES metadata_pipeline_run(pipeline_run_id),
        table_name TEXT NOT NULL,
        metric_name TEXT NOT NULL,
        metric_value REAL,
        year INTEGER CHECK (year IS NULL OR year BETWEEN 1900 AND 2100),
        scope TEXT,
        notes TEXT,
        created_timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
)


INDEX_STATEMENTS: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS idx_ref_geography_cbsa ON ref_geography(cbsa_code);",
    "CREATE INDEX IF NOT EXISTS idx_ref_geography_county_cbsa ON ref_geography_county_crosswalk(cbsa_code);",
    "CREATE INDEX IF NOT EXISTS idx_ref_geography_county_geoid ON ref_geography_county_crosswalk(county_geoid);",
    "CREATE INDEX IF NOT EXISTS idx_ref_industry_naics ON ref_industry(naics_code);",
    "CREATE INDEX IF NOT EXISTS idx_manifest_source_year ON metadata_source_manifest(source_id, source_year);",
    "CREATE INDEX IF NOT EXISTS idx_pipeline_run_status_stage ON metadata_pipeline_run(status, stage);",
    "CREATE INDEX IF NOT EXISTS idx_raw_bds_source_keys ON raw_bds(source_geography_id, source_industry_id, source_year);",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_bds_file_row ON raw_bds(raw_source_filename, source_row_identifier);",
    "CREATE INDEX IF NOT EXISTS idx_raw_bds_firm_age_source_keys ON raw_bds_firm_age(source_geography_id, source_industry_id, source_year, source_fagecoarse);",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_bds_firm_age_file_row ON raw_bds_firm_age(raw_source_filename, source_row_identifier);",
    "CREATE INDEX IF NOT EXISTS idx_raw_qcew_source_keys ON raw_qcew(source_geography_id, source_industry_id, source_year);",
    "CREATE INDEX IF NOT EXISTS idx_raw_qcew_ownership ON raw_qcew(source_ownership_code, source_year);",
    "CREATE INDEX IF NOT EXISTS idx_raw_cbp_source_keys ON raw_cbp(source_geography_id, source_industry_id, source_year);",
    "CREATE INDEX IF NOT EXISTS idx_raw_acs_source_keys ON raw_acs(source_geography_id, source_year);",
    "CREATE INDEX IF NOT EXISTS idx_stg_bds_grain ON stg_bds(geography_id, industry_id, year);",
    "CREATE INDEX IF NOT EXISTS idx_stg_qcew_grain ON stg_qcew(geography_id, industry_id, year);",
    "CREATE INDEX IF NOT EXISTS idx_stg_cbp_grain ON stg_cbp(geography_id, industry_id, year);",
    "CREATE INDEX IF NOT EXISTS idx_stg_acs_grain ON stg_acs(geography_id, year);",
    "CREATE INDEX IF NOT EXISTS idx_int_entrepreneurship_year ON int_entrepreneurship(year);",
    "CREATE INDEX IF NOT EXISTS idx_int_industry_growth_year ON int_industry_growth(year);",
    "CREATE INDEX IF NOT EXISTS idx_int_regional_controls_year ON int_regional_controls(year);",
    "CREATE INDEX IF NOT EXISTS idx_int_business_structure_year ON int_business_structure(year);",
    "CREATE INDEX IF NOT EXISTS idx_analytics_year ON analytics_msa_industry_year(year);",
    "CREATE INDEX IF NOT EXISTS idx_rejected_run_reason ON quality_rejected_record(pipeline_run_id, reason_code);",
    "CREATE INDEX IF NOT EXISTS idx_quality_metric_run_table ON quality_table_metric(pipeline_run_id, table_name);",
)


PRIMARY_STUDY_YEARS = tuple(range(2010, 2024))


def create_schema(connection: sqlite3.Connection, *, seed_years: bool = True) -> None:
    """Create all Assignment 4.2 schema objects.

    The function is intentionally idempotent and safe to rerun.
    """
    connection.execute("PRAGMA foreign_keys = ON;")
    with connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        for statement in INDEX_STATEMENTS:
            connection.execute(statement)
        if seed_years:
            seed_ref_year(connection)


def seed_ref_year(connection: sqlite3.Connection) -> None:
    """Populate deterministic primary study years without loading source data."""
    connection.executemany(
        """
        INSERT INTO ref_year (year, is_primary_study_year, notes)
        VALUES (?, 1, 'Primary Assignment 4 study window')
        ON CONFLICT(year) DO UPDATE SET
            is_primary_study_year = excluded.is_primary_study_year,
            notes = excluded.notes;
        """,
        [(year,) for year in PRIMARY_STUDY_YEARS],
    )


def initialize_database(database_path: str | Path | None = None) -> Path:
    """Create or update the SQLite schema and return the database path."""
    path = Path(database_path) if database_path is not None else DEFAULT_DATABASE_PATH
    with connect_database(path) as connection:
        create_schema(connection)
    return path


def main() -> None:
    """CLI entry point for schema initialization."""
    parser = argparse.ArgumentParser(description="Initialize the project SQLite schema.")
    parser.add_argument(
        "--database-path",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the SQLite database file.",
    )
    args = parser.parse_args()
    database_path = initialize_database(args.database_path)
    print(f"Initialized schema at {database_path}")


if __name__ == "__main__":
    main()
