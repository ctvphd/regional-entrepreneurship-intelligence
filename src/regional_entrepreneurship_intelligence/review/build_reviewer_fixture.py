"""Build a synthetic A4 end-to-end review database without production inputs."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path

import pandas as pd

from regional_entrepreneurship_intelligence.database.connection import PROJECT_ROOT, connect_database
from regional_entrepreneurship_intelligence.database.reference import (
    GEOGRAPHY_VINTAGE, load_authoritative_reference_data,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.build_analytics_panel import build_panel
from regional_entrepreneurship_intelligence.etl.extract_acs import load_acs_raw
from regional_entrepreneurship_intelligence.etl.extract_bds import load_bds_firm_age_raw, load_bds_raw
from regional_entrepreneurship_intelligence.etl.extract_cbp import load_cbp_raw
from regional_entrepreneurship_intelligence.etl.extract_qcew import load_qcew_raw
from regional_entrepreneurship_intelligence.etl.transform_acs import build_acs_regional_controls
from regional_entrepreneurship_intelligence.etl.transform_bds import build_bds_standardized_layers
from regional_entrepreneurship_intelligence.etl.transform_cbp import build_cbp_business_structure
from regional_entrepreneurship_intelligence.etl.transform_qcew import build_qcew_standardized_layers


ROOT = PROJECT_ROOT
SOURCE_DIR = ROOT / "tests" / "fixtures" / "reviewer_sources"
REVIEW_DIR = ROOT / "data" / "review"
DEFAULT_DATABASE = REVIEW_DIR / "reviewer_fixture.sqlite"
SYNTHETIC_CBSAS = (("99901", "Synthetic Metro Alpha", "99001"), ("99902", "Synthetic Metro Beta", "99003"))
SECTORS = (("11", "Synthetic sector 11"), ("54", "Synthetic sector 54"))
ACS_CONTROLS = ("population", "median_household_income", "educational_attainment_pct", "labor_force_participation_pct", "unemployment_rate")
ACS_REGISTRY = ROOT / "data" / "external" / "reference" / "acs_variable_registry.csv"


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sources(directory: Path = SOURCE_DIR) -> list[Path]:
    """Materialize small, deterministic source-shaped records with fictional values."""
    directory.mkdir(parents=True, exist_ok=True)
    bds_fields = ["year", "msa", "sector", "firms", "estabs", "emp", "denom", "estabs_entry", "estabs_entry_rate", "estabs_exit", "estabs_exit_rate", "job_creation", "job_creation_births", "job_creation_continuers", "job_creation_rate_births", "job_creation_rate", "job_destruction", "job_destruction_deaths", "job_destruction_continuers", "job_destruction_rate_deaths", "job_destruction_rate", "net_job_creation", "net_job_creation_rate", "reallocation_rate", "firmdeath_firms", "firmdeath_estabs", "firmdeath_emp"]
    bds_rows, age_rows = [], []
    for year in range(2010, 2024):
        for cbsa, _name, _county in SYNTHETIC_CBSAS:
            for sector, _title in SECTORS:
                bds_rows.append(dict(zip(bds_fields, [str(year), cbsa, sector, "20", "22", "80", "20", "2", "10.0", "1", "5.0", "12", "4", "8", "5.0", "15.0", "6", "2", "4", "2.5", "7.5", "6", "7.5", "22.5", "1", "1", "3"])))
                age0 = "D" if (year, cbsa, sector) == (2019, "99902", "54") else "0" if (year, cbsa, sector) == (2018, "99901", "11") else "3"
                age_rows.append({**dict(zip(bds_fields, [str(year), cbsa, sector, age0, "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])), "fagecoarse": "a) 0"})
    # An unmapped synthetic geography/industry row audits explicit exclusion.
    bds_rows.append(dict(zip(bds_fields, ["2020", "99888", "98", "7", "8", "20", "7", "1", "14.3", "0", "0.0", "4", "2", "2", "10.0", "20.0", "1", "0", "1", "0.0", "5.0", "3", "15.0", "25.0", "0", "0", "0"])))
    age_rows.append({**dict(zip(bds_fields, ["2020", "99888", "98", "2", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])), "fagecoarse": "a) 0"})
    paths = []
    for name, fields, rows in (("bds_msa_sector.csv", bds_fields, bds_rows), ("bds_msa_sector_age.csv", bds_fields + ["fagecoarse"], age_rows)):
        path = directory / name; _write_csv(path, fields, rows); paths.append(path)

    qcew_fields = ["area_fips", "own_code", "industry_code", "agglvl_code", "size_code", "year", "qtr", "disclosure_code", "annual_avg_estabs", "annual_avg_emplvl", "total_annual_wages", "avg_annual_pay"]
    qcew_rows = []
    for year in range(2017, 2024):
        for _cbsa, _name, county in SYNTHETIC_CBSAS:
            for sector in ("11", "54"):
                employment = 100 + (year - 2017) * 10 + int(sector)
                qcew_rows.append(dict(zip(qcew_fields, [county, "5", sector, "71", "0", str(year), "A", "", "10", str(employment), str(employment * 42000), "42000"])))
    path = directory / "qcew_county_sector.csv"; _write_csv(path, qcew_fields, qcew_rows); paths.append(path)

    with ACS_REGISTRY.open(encoding="utf-8", newline="") as stream:
        registry = {(int(row["year"]), row["concept_name"]): row for row in csv.DictReader(stream)}
    acs_fields = ["source_year", "acs_product", "source_geography_id", "source_geography_name", "control_name", "variable_id", "moe_variable_id", "estimate", "margin_of_error", "variable_label", "official_api_url", "raw_response"]
    acs_rows = []
    for year in range(2017, 2024):
        for cbsa, name, _county in SYNTHETIC_CBSAS:
            for index, control in enumerate(ACS_CONTROLS):
                metadata = registry[year, control]
                estimate = "" if (year, cbsa, control) == (2020, "99902", "unemployment_rate") else str((100000 + index * 1000 + year) if control in {"population", "median_household_income"} else 50 + index)
                acs_rows.append({"source_year": str(year), "acs_product": "Synthetic ACS profile", "source_geography_id": cbsa, "source_geography_name": name, "control_name": control, "variable_id": metadata["variable_id"], "moe_variable_id": metadata["moe_variable_id"], "estimate": estimate, "margin_of_error": "5", "variable_label": metadata["variable_label"], "official_api_url": "synthetic://acs", "raw_response": json.dumps({"synthetic": True, "control": control}, sort_keys=True)})
    path = directory / "acs_metro_controls.csv"; _write_csv(path, acs_fields, acs_rows); paths.append(path)

    cbp_fields = ["source_year", "cbp_product", "state_fips", "county_fips", "county_geoid", "county_name", "source_industry_id", "source_industry_label", "source_naics_version", "legal_form_code", "employment_size_code", "establishments", "establishments_flag", "employment", "employment_flag", "annual_payroll", "annual_payroll_flag", "first_quarter_payroll", "first_quarter_payroll_flag", "official_api_url", "raw_response"]
    cbp_rows = []
    for year in (2022, 2023):
        for _cbsa, _name, county in SYNTHETIC_CBSAS:
            for sector, title in SECTORS:
                cbp_rows.append(dict(zip(cbp_fields, [str(year), "Synthetic CBP", county[:2], county[2:], county, "Synthetic County", sector, title, "2017", "001", "001", "10", "", "80", "", "4000", "", "1000", "", "synthetic://cbp", json.dumps({"synthetic": True}, sort_keys=True)])))
    path = directory / "cbp_county_sector.csv"; _write_csv(path, cbp_fields, cbp_rows); paths.append(path)

    geo_fields = ["cbsa_code", "cbsa_name", "county_geoid", "county_name", "state_fips", "county_fips", "source_vintage"]
    geo_rows = [{"cbsa_code": cbsa, "cbsa_name": name, "county_geoid": county, "county_name": "Synthetic County", "state_fips": county[:2], "county_fips": county[2:], "source_vintage": GEOGRAPHY_VINTAGE} for cbsa, name, county in SYNTHETIC_CBSAS]
    path = directory / "synthetic_cbsa_county_crosswalk.csv"; _write_csv(path, geo_fields, geo_rows); paths.append(path)
    ind_fields = ["native_version", "source_sector", "target_2022_sector", "mapping_status"]
    path = directory / "synthetic_naics_crosswalk.csv"; _write_csv(path, ind_fields, [{"native_version": "2017", "source_sector": sector, "target_2022_sector": sector, "mapping_status": "directly_comparable"} for sector, _ in SECTORS] + [{"native_version": "2017", "source_sector": "98", "target_2022_sector": "", "mapping_status": "unmatched synthetic edge case"}]); paths.append(path)
    return paths


def _load_synthetic_geography(connection: sqlite3.Connection, crosswalk: Path) -> None:
    with crosswalk.open(encoding="utf-8", newline="") as stream:
        records = list(csv.DictReader(stream))
    for row in records:
        connection.execute("INSERT OR IGNORE INTO ref_geography (cbsa_code, cbsa_name, geography_type, state_codes, source_vintage, is_active, notes) VALUES (?, ?, 'MSA', ?, ?, 1, 'Synthetic reviewer fixture; not a real place.')", (row["cbsa_code"], row["cbsa_name"], row["state_fips"], row["source_vintage"]))
    ids = {code: gid for code, gid in connection.execute("SELECT cbsa_code, geography_id FROM ref_geography WHERE source_vintage=?", (GEOGRAPHY_VINTAGE,))}
    for row in records:
        connection.execute("INSERT OR IGNORE INTO ref_geography_county_crosswalk (geography_id, cbsa_code, county_name, state_name, state_fips, county_fips, county_geoid, central_outlying, source_vintage, notes) VALUES (?, ?, ?, 'Synthetic State', ?, ?, ?, 'Central', ?, 'Synthetic reviewer fixture mapping.')", (ids[row["cbsa_code"]], row["cbsa_code"], row["county_name"], row["state_fips"], row["county_fips"], row["county_geoid"], row["source_vintage"]))


def build(database_path: Path = DEFAULT_DATABASE, source_dir: Path = SOURCE_DIR) -> dict[str, object]:
    sources = write_sources(source_dir)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect_database(database_path)
    try:
        create_schema(connection)
        load_authoritative_reference_data(connection)
        _load_synthetic_geography(connection, source_dir / "synthetic_cbsa_county_crosswalk.csv")
        load_bds_raw(connection, source_dir / "bds_msa_sector.csv", official_source_url="synthetic://bds", source_version="synthetic reviewer fixture")
        load_bds_firm_age_raw(connection, source_dir / "bds_msa_sector_age.csv", official_source_url="synthetic://bds-age", source_version="synthetic reviewer fixture")
        load_qcew_raw(connection, source_dir / "qcew_county_sector.csv", official_source_url="synthetic://qcew", source_version="synthetic reviewer fixture")
        load_acs_raw(connection, source_dir / "acs_metro_controls.csv", official_source_url="synthetic://acs", source_version="synthetic reviewer fixture")
        load_cbp_raw(connection, source_dir / "cbp_county_sector.csv", official_source_url="synthetic://cbp", source_version="synthetic reviewer fixture")
        build_bds_standardized_layers(connection, load_raw_if_missing=False)
        build_qcew_standardized_layers(connection, load_raw_if_missing=False)
        build_acs_regional_controls(connection, load_raw_if_missing=False)
        build_cbp_business_structure(connection, load_raw_if_missing=False)
        build_panel(connection)
        duplicate_keys = connection.execute("SELECT COUNT(*) FROM (SELECT geography_id,industry_id,year FROM analytics_msa_industry_year GROUP BY geography_id,industry_id,year HAVING COUNT(*)>1)").fetchone()[0]
        fk_violations = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        suppressed_startups = connection.execute("SELECT COUNT(*) FROM stg_bds WHERE source_geography_id='99902' AND source_industry_id='54' AND year=2019 AND is_suppressed=1").fetchone()[0]
        suppressed_core_rows = connection.execute("SELECT COUNT(*) FROM analytics_msa_industry_year a JOIN ref_geography g USING(geography_id) JOIN ref_industry i USING(industry_id) WHERE g.cbsa_code='99902' AND i.naics_code='54' AND a.year=2019").fetchone()[0]
        if duplicate_keys or fk_violations or suppressed_startups != 1 or suppressed_core_rows:
            raise AssertionError("Synthetic reviewer fixture quality checks failed")
        quality_check_count = 4
        summary = {
            "label": "Synthetic reviewer fixture",
            "source_files": len(sources),
            "analytical_rows": connection.execute("SELECT COUNT(*) FROM analytics_msa_industry_year").fetchone()[0],
            "msa_count": connection.execute("SELECT COUNT(*) FROM (SELECT DISTINCT g.cbsa_code FROM analytics_msa_industry_year a JOIN ref_geography g USING(geography_id))").fetchone()[0],
            "sector_count": connection.execute("SELECT COUNT(DISTINCT i.naics_code) FROM analytics_msa_industry_year a JOIN ref_industry i USING(industry_id)").fetchone()[0],
            "year_min_max": list(connection.execute("SELECT MIN(year), MAX(year) FROM analytics_msa_industry_year").fetchone()),
            "duplicate_keys": duplicate_keys,
            "quality_check_count": quality_check_count,
            "database_path": str(database_path),
        }
        summary["foreign_key_violations"] = fk_violations
        review_data = database_path.parent / "dashboard"
        review_data.mkdir(parents=True, exist_ok=True)
        panel = pd.read_sql_query("SELECT * FROM v_analytics_msa_industry_year ORDER BY cbsa_code, sector_code, year", connection)
        panel.to_parquet(review_data / "dashboard_msa_industry_year.parquet", index=False, engine="pyarrow")
        (review_data / "dashboard_metadata.json").write_text(json.dumps({"fixture": "synthetic reviewer fixture", "unit_of_analysis": "CBSA x 2-digit NAICS sector x year", "production_metrics": False}, indent=2) + "\n", encoding="utf-8")
        summary["dashboard_review_path"] = str(review_data)
        return summary
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-path", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    result = build(args.database_path)
    print(json.dumps(result, indent=2, default=list))


if __name__ == "__main__":
    main()
