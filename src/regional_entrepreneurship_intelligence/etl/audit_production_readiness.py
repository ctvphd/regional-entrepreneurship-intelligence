"""Audit four source-specific intermediate tables without joining their measures."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from regional_entrepreneurship_intelligence.database.connection import connect_database
from regional_entrepreneurship_intelligence.database.metadata import (
    finish_pipeline_run, insert_quality_metric, start_pipeline_run,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.run_bds_production import PRODUCTION_DATABASE


TABLES = {
    "BDS": "v_bds_metropolitan_eligible",
    "QCEW": "int_industry_growth",
    "ACS": "int_regional_controls",
    "CBP": "int_business_structure",
}
RAW_TABLES = {"BDS": "raw_bds", "QCEW": "raw_qcew", "ACS": "raw_acs", "CBP": "raw_cbp"}


def _metro_codes(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[0] for row in connection.execute(f"""
        SELECT DISTINCT g.cbsa_code FROM {table} AS t
        JOIN ref_geography AS g ON g.geography_id = t.geography_id
        WHERE g.geography_type = 'MSA'
    """)}


def _sectors(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[0] for row in connection.execute(f"""
        SELECT DISTINCT i.naics_code FROM {table} AS t
        JOIN ref_industry AS i ON i.industry_id = t.industry_id
    """)}


def audit(connection: sqlite3.Connection) -> dict:
    create_schema(connection)
    run_id = start_pipeline_run(connection, stage="cross_source_readiness_audit")
    geographies = {source: _metro_codes(connection, table) for source, table in TABLES.items()}
    industries = {source: _sectors(connection, TABLES[source]) for source in ("BDS", "QCEW", "CBP")}
    common_geographies = set.intersection(*geographies.values())
    common_industries = set.intersection(*industries.values())
    years = []
    for year in range(2010, 2024):
        row = {"year": year}
        for source, table in TABLES.items():
            raw_count = connection.execute(
                f"SELECT COUNT(*) FROM {RAW_TABLES[source]} WHERE source_year = ?", (year,)
            ).fetchone()[0]
            final_count = connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE year = ?", (year,)
            ).fetchone()[0]
            if raw_count == 0:
                status, reason = "blocked", "no national source rows loaded"
            elif final_count == 0:
                status, reason = "blocked", "raw rows loaded but no standardized intermediate rows"
            else:
                status, reason = "ready", "source-specific intermediate rows available; cell missingness audited separately"
            row[source] = {"status": status, "reason": reason, "raw_rows": raw_count,
                           "intermediate_rows": final_count}
            insert_quality_metric(
                connection, pipeline_run_id=run_id, table_name="a411b_year_readiness",
                metric_name=f"{source.lower()}_intermediate_rows", metric_value=float(final_count),
                year=year, scope=status, notes=reason,
            )
        years.append(row)
    result = {
        "metropolitan_geography_counts": {source: len(codes) for source, codes in geographies.items()},
        "common_metropolitan_count": len(common_geographies),
        "common_metropolitan_codes": sorted(common_geographies),
        "source_only_metropolitan_codes": {
            source: sorted(codes - set.union(*(other for name, other in geographies.items() if name != source)))
            for source, codes in geographies.items()
        },
        "industry_sectors": {source: sorted(codes) for source, codes in industries.items()},
        "common_industry_sectors": sorted(common_industries),
        "year_readiness": years,
    }
    for source, codes in geographies.items():
        insert_quality_metric(
            connection, pipeline_run_id=run_id, table_name="a411b_cross_source",
            metric_name=f"{source.lower()}_metro_cbsas", metric_value=float(len(codes)),
            scope="metropolitan geography coverage",
        )
    insert_quality_metric(
        connection, pipeline_run_id=run_id, table_name="a411b_cross_source",
        metric_name="four_source_common_metro_cbsas", metric_value=float(len(common_geographies)),
        scope="metropolitan geography coverage",
    )
    connection.commit()
    finish_pipeline_run(connection, run_id, records_read=sum(
        row[source]["raw_rows"] for row in years for source in TABLES
    ), records_written=0)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-path", type=Path, default=PRODUCTION_DATABASE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with connect_database(args.database_path) as connection:
        result = audit(connection)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in {
        "common_metropolitan_codes", "source_only_metropolitan_codes", "year_readiness"
    }}, indent=2))


if __name__ == "__main__":
    main()
