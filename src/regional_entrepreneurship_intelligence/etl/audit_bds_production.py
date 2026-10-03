"""Audit national BDS startup missingness without changing source layers."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from regional_entrepreneurship_intelligence.database.connection import connect_database
from regional_entrepreneurship_intelligence.database.metadata import (
    finish_pipeline_run,
    insert_quality_metric,
    start_pipeline_run,
)
from regional_entrepreneurship_intelligence.etl.run_bds_production import PRODUCTION_DATABASE


def missing_reason(numerator: object, denominator: object, geography: str, industry: str) -> str:
    """Classify only the first cause supported by source and mapping evidence."""
    if geography != "direct_match":
        return "geography_mismatch"
    if industry not in {"directly_comparable", "official_mapping_required"}:
        return "industry_mismatch"
    for value, role in ((numerator, "numerator"), (denominator, "denominator")):
        code = "" if value is None else str(value).strip()
        if code in {"D", "S"}:
            return f"{role}_suppressed"
        if code in {"", "N", "X"}:
            return f"{role}_missing"
        try:
            number = float(code)
        except ValueError:
            return f"{role}_missing"
        if role == "denominator" and number == 0:
            return "denominator_zero"
    return "other"


def audit(connection: sqlite3.Connection) -> dict:
    """Persist quality metrics and return a dimensioned BDS readiness audit."""
    run_id = start_pipeline_run(connection, stage="bds_production_readiness_audit")
    reasons = Counter()
    by_year = defaultdict(Counter)
    by_sector = defaultdict(Counter)
    by_msa = defaultdict(Counter)
    by_scope = defaultdict(Counter)
    by_suppression = defaultdict(Counter)
    query = """
        SELECT s.year, s.source_geography_id, s.source_industry_id,
               s.geography_mapping_status, s.industry_mapping_status,
               s.startup_rate, s.is_suppressed,
               COALESCE(g.geography_type, 'UNRESOLVED'),
               json_extract(a.raw_payload, '$.firms'),
               json_extract(b.raw_payload, '$.firms')
        FROM stg_bds AS s
        JOIN raw_bds_firm_age AS a
          ON a.source_year = s.year
         AND a.source_geography_id = s.source_geography_id
         AND a.source_industry_id = s.source_industry_id
         AND a.source_fagecoarse = s.source_fagecoarse
        LEFT JOIN raw_bds AS b
          ON b.source_year = s.year
         AND b.source_geography_id = s.source_geography_id
         AND b.source_industry_id = s.source_industry_id
        LEFT JOIN ref_geography AS g ON g.geography_id = s.geography_id
    """
    total = 0
    missing = 0
    metro_complete = 0
    metro_missing = 0
    for year, msa, sector, geo_status, ind_status, rate, suppressed, scope, numerator, denominator in connection.execute(query):
        total += 1
        if scope == "MSA":
            if rate is None:
                metro_missing += 1
            else:
                metro_complete += 1
        if rate is not None:
            continue
        missing += 1
        reason = missing_reason(numerator, denominator, geo_status, ind_status)
        reasons[reason] += 1
        for dimension, value in (
            (by_year, str(year)), (by_sector, sector), (by_msa, msa),
            (by_scope, scope), (by_suppression, str(int(bool(suppressed)))),
        ):
            dimension[value][reason] += 1
    if total != connection.execute("SELECT COUNT(*) FROM stg_bds").fetchone()[0]:
        raise ValueError("BDS audit join is not one-to-one; inspect source duplicates")
    if missing != connection.execute("SELECT COUNT(*) FROM stg_bds WHERE startup_rate IS NULL").fetchone()[0]:
        raise ValueError("BDS audit missingness count differs from staging")
    metro = connection.execute("""
        SELECT COUNT(*), COUNT(DISTINCT e.geography_id), COUNT(DISTINCT e.industry_id),
               COUNT(DISTINCT e.year),
               SUM(e.startup_rate_lag1 IS NOT NULL),
               SUM(e.startup_rate_lag2 IS NOT NULL),
               SUM(e.startup_rate_lag3 IS NOT NULL),
               SUM(e.has_suppression)
        FROM int_entrepreneurship AS e
        JOIN ref_geography AS g ON g.geography_id = e.geography_id
        WHERE g.geography_type = 'MSA'
    """).fetchone()
    metrics = {
        "staged_rows": total,
        "startup_missing_rows": missing,
        "metro_startup_complete_rows": metro_complete,
        "metro_startup_missing_rows": metro_missing,
        "metro_intermediate_rows": metro[0],
        "metro_msas": metro[1],
        "metro_sectors": metro[2],
        "metro_years": metro[3],
        "metro_lag1_available": metro[4],
        "metro_lag2_available": metro[5],
        "metro_lag3_available": metro[6],
        "metro_suppressed_rows": metro[7],
    }
    with connection:
        for name, value in {**metrics, **{f"missing_{reason}": count for reason, count in reasons.items()}}.items():
            insert_quality_metric(
                connection, pipeline_run_id=run_id, table_name="bds_a411b",
                metric_name=name, metric_value=float(value), scope="national BDS production",
            )
    finish_pipeline_run(connection, run_id, records_read=total, records_written=0)
    return {
        "metrics": metrics,
        "reasons": dict(sorted(reasons.items())),
        "reason_percentages": {
            reason: round(count / missing * 100, 2) if missing else 0.0
            for reason, count in sorted(reasons.items())
        },
        "by_year": {k: dict(v) for k, v in sorted(by_year.items())},
        "by_sector": {k: dict(v) for k, v in sorted(by_sector.items())},
        "by_scope": {k: dict(v) for k, v in sorted(by_scope.items())},
        "by_suppression": {k: dict(v) for k, v in sorted(by_suppression.items())},
        "by_msa": {k: dict(v) for k, v in sorted(by_msa.items())},
    }


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
    print(json.dumps({"metrics": result["metrics"], "reasons": result["reasons"]}, indent=2))


if __name__ == "__main__":
    main()
