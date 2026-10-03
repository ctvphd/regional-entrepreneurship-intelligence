"""Count historical NAICS mapping outcomes by source and year."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

from regional_entrepreneurship_intelligence.database.connection import connect_database
from regional_entrepreneurship_intelligence.database.metadata import (
    finish_pipeline_run, insert_quality_metric, start_pipeline_run,
)
from regional_entrepreneurship_intelligence.database.naics_versions import (
    classify_sector, source_year_naics,
)
from regional_entrepreneurship_intelligence.etl.run_bds_production import PRODUCTION_DATABASE


TABLES = {"QCEW": "raw_qcew", "CBP": "raw_cbp"}


def audit(connection: sqlite3.Connection) -> list[dict]:
    run_id = start_pipeline_run(connection, stage="source_naics_version_audit")
    output = []
    for source, table in TABLES.items():
        for year in range(2010, 2024):
            expected = source_year_naics(source, year).native_version
            rows = connection.execute(f"""
                SELECT source_naics_version, source_industry_id, COUNT(*)
                FROM {table} WHERE source_year = ?
                GROUP BY source_naics_version, source_industry_id
            """, (year,)).fetchall()
            counts = Counter()
            sectors = set()
            excluded = set()
            for vintage, sector, count in rows:
                if vintage != expected:
                    raise ValueError(f"{source}/{year} stored {vintage}, expected {expected}")
                status, target = classify_sector(vintage, sector)
                counts[status] += count
                if target is not None:
                    sectors.add(target)
                else:
                    excluded.add(sector)
            total = sum(counts.values())
            record = {
                "source": source, "year": year, "native_naics": expected,
                "source_rows": total,
                "directly_comparable_rows": counts["directly_comparable"],
                "officially_mapped_rows": counts["official_mapping_required"],
                "unresolved_rows": counts["unresolved"],
                "retained_sectors": sorted(sectors),
                "excluded_sectors": sorted(excluded),
            }
            output.append(record)
            for name in ("source_rows", "directly_comparable_rows", "officially_mapped_rows", "unresolved_rows"):
                insert_quality_metric(
                    connection, pipeline_run_id=run_id, table_name=f"{source.lower()}_version_audit",
                    metric_name=name, metric_value=float(record[name]), year=year,
                    scope=f"{expected} NAICS to 2022 broad sector",
                )
    finish_pipeline_run(connection, run_id, records_read=sum(row["source_rows"] for row in output),
                        records_written=0)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-path", type=Path, default=PRODUCTION_DATABASE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with connect_database(args.database_path) as connection:
        rows = audit(connection)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
