"""Run the complete cache-first Assignment 4 production pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from regional_entrepreneurship_intelligence.database.connection import PROJECT_ROOT, connect_database
from regional_entrepreneurship_intelligence.database.metadata import finish_pipeline_run, start_pipeline_run
from regional_entrepreneurship_intelligence.database.reference import load_authoritative_reference_data
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.build_analytics_panel import build_panel
from regional_entrepreneurship_intelligence.etl.run_acs_production import PRODUCTION_DIR as ACS_DIR, run as run_acs
from regional_entrepreneurship_intelligence.etl.run_bds_production import PRODUCTION_DATABASE, PRODUCTION_DIR as BDS_DIR, run as run_bds
from regional_entrepreneurship_intelligence.etl.run_cbp_production import PRODUCTION_DIR as CBP_DIR, run as run_cbp
from regional_entrepreneurship_intelligence.etl.run_qcew_production import PRODUCTION_DIR as QCEW_DIR, run as run_qcew
from regional_entrepreneurship_intelligence.validation.checks import (
    validate_no_leakage_columns,
    validate_unique_key,
    validate_year_range,
)


DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"
DEFAULT_EXPORT = PROJECT_ROOT / "data/processed/analytics_msa_industry_year.csv.gz"
DEFAULT_REPORT = PROJECT_ROOT / "reports/assignment4_merge_audit.md"
LEAKAGE_COLUMNS = (
    "expected_entrepreneurship", "alignment_residual", "entrepreneurial_gap",
    "future_outcome", "model_prediction",
)


def required_production_inputs() -> list[Path]:
    """List the existing national production cache required for offline runs."""
    files = [BDS_DIR / name for name in (
        "bds2023_msa_sec.csv", "bds2023_msa_sec_fac.csv",
    )]
    files += [QCEW_DIR / f"{year}_annual_by_area.zip" for year in range(2010, 2024)]
    files += [QCEW_DIR / f"qcew_private_county_sector_{year}.csv" for year in range(2010, 2024)]
    files += [ACS_DIR / f"acs5_profile_metro_{year}.csv" for year in range(2010, 2024)]
    files += [CBP_DIR / f"cbp_county_sector_{year}.csv" for year in range(2010, 2024)]
    return files


def _table_count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])


def _stage_log(logger: logging.Logger, name: str, action: Callable[[], Any]) -> Any:
    started = time.monotonic()
    logger.info("stage_start name=%s", name)
    try:
        result = action()
    except Exception:
        logger.exception("stage_failed name=%s", name)
        raise
    logger.info("stage_success name=%s runtime_seconds=%.1f", name, time.monotonic() - started)
    return result


def run_pipeline(
    database_path: Path = PRODUCTION_DATABASE,
    *,
    allow_downloads: bool = False,
    log_dir: Path = DEFAULT_LOG_DIR,
) -> dict[str, Any]:
    """Orchestrate references, four source pipelines, integration, and QA."""
    missing = [path for path in required_production_inputs() if not path.is_file()]
    if missing and not allow_downloads:
        sample = "\n".join(f"  - {path}" for path in missing[:12])
        more = f"\n  ... and {len(missing) - 12} more" if len(missing) > 12 else ""
        raise FileNotFoundError(
            f"Cache-only production run is missing {len(missing)} required inputs. "
            "Restore the production files or rerun with --allow-downloads:\n" + sample + more
        )

    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"assignment4_pipeline_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid.uuid4().hex[:8]}.log"
    logger = logging.getLogger(f"assignment4_pipeline.{uuid.uuid4().hex}")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    started_at = datetime.now(timezone.utc).isoformat()
    wall_start = time.monotonic()
    logger.info("pipeline_start allow_downloads=%s database=%s", allow_downloads, database_path)
    run_id = None
    run_id_holder: list[str | None] = [None]
    try:
        def initialize() -> dict[str, int]:
            with connect_database(database_path) as connection:
                create_schema(connection)
                run_id_holder[0] = start_pipeline_run(connection, stage="assignment4_end_to_end")
                reference = load_authoritative_reference_data(connection)
                return {
                    "geographies": reference.ref_geography_count,
                    "county_crosswalk_rows": reference.ref_geography_county_crosswalk_count,
                    "industries": reference.ref_industry_count,
                }

        reference_counts = _stage_log(logger, "initialize_schema_and_references", initialize)
        run_id = run_id_holder[0]
        stages: dict[str, Any] = {"references": reference_counts}
        source_stages = (
            ("bds", run_bds), ("qcew", run_qcew),
            ("acs", run_acs), ("cbp", run_cbp),
        )
        for name, runner in source_stages:
            stages[name] = _stage_log(
                logger, f"source_{name}", lambda runner=runner: runner(database_path)
            )
            logger.info("source_summary name=%s summary=%s", name, json.dumps(stages[name], default=str))

        export_path = PROJECT_ROOT / "data/processed/analytics_msa_industry_year.csv.gz"
        merge_report_path = PROJECT_ROOT / "reports/assignment4_merge_audit.md"
        panel_result = _stage_log(logger, "integrate_analytics_panel", lambda: _build_panel(
            database_path, export_path, merge_report_path
        ))
        with connect_database(database_path) as connection:
            def validate() -> dict[str, int]:
                duplicate_count = validate_unique_key(
                    connection, "analytics_msa_industry_year", ("geography_id", "industry_id", "year")
                )
                validate_year_range(connection, "analytics_msa_industry_year", "year", 2010, 2023)
                validate_no_leakage_columns(connection, "analytics_msa_industry_year", LEAKAGE_COLUMNS)
                out_of_scope = connection.execute("""SELECT COUNT(*) FROM analytics_msa_industry_year a
                    JOIN ref_geography g USING(geography_id) WHERE g.geography_type <> 'MSA'""").fetchone()[0]
                if out_of_scope:
                    raise ValueError(f"Analytics contains {out_of_scope} non-MSA rows")
                return {"duplicate_keys": duplicate_count, "out_of_scope_rows": int(out_of_scope)}

            validation = _stage_log(logger, "final_validation", validate)
            counts = {
                table: _table_count(connection, table) for table in (
                    "raw_bds", "raw_bds_firm_age", "stg_bds", "int_entrepreneurship",
                    "raw_qcew", "stg_qcew", "int_industry_growth", "raw_acs", "stg_acs",
                    "int_regional_controls", "raw_cbp", "stg_cbp", "int_business_structure",
                    "analytics_msa_industry_year",
                )
            }
            rejections = [
                    {"table_name": row[0], "stage": row[1], "reason_code": row[2], "records": row[3]}
                for row in connection.execute("""
                    SELECT r.table_name, r.stage, r.reason_code, COUNT(*) AS records
                    FROM quality_rejected_record r
                    GROUP BY r.table_name, r.stage, r.reason_code
                    ORDER BY r.table_name, r.stage, r.reason_code
                """)
            ]
            quality_metrics = {
                str(row[0]): float(row[1])
                for row in connection.execute("""
                    SELECT metric_name, metric_value FROM quality_table_metric
                    WHERE pipeline_run_id = ? AND table_name = 'analytics_msa_industry_year'
                    ORDER BY metric_name
                """, (panel_result["pipeline_run_id"],))
            }
            source_rejections = {
                name: int(stages[name].get("rejected_rows", 0))
                for name, _runner in source_stages
            }
            records_rejected = sum(source_rejections.values())
            warning_counts = {
                "bds_missing_startup_measure": int(stages["bds"].get("missing_startup_rows", 0)),
                "qcew_incomplete_aggregation": int(stages["qcew"].get("incomplete_aggregation_rows", 0)),
                "acs_unresolved_geography": int(stages["acs"].get("geography_audit", {}).get("unresolved", 0)),
                "cbp_incomplete_aggregation": int(stages["cbp"].get("incomplete_aggregation_rows", 0)),
            }
            warning_count = sum(warning_counts.values())
            records_read = sum(value for key, value in counts.items() if key.startswith("raw_"))
            records_written = sum(value for key, value in counts.items() if key.startswith("int_")) + counts["analytics_msa_industry_year"]

        panel_fields = (
            "final_rows", "metropolitan_msas", "industries", "minimum_year", "maximum_year",
            "msa_industry_panels", "balanced_panels_14_years", "unbalanced_panels", "duplicate_keys",
        )
        panel_summary = {key: panel_result["panel"][key] for key in panel_fields}
        result = {
            "status": "success", "started_at": started_at,
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "runtime_seconds": round(time.monotonic() - wall_start, 1),
            "pipeline_run_id": run_id, "database_path": str(database_path),
            "log_path": str(log_path), "stage_counts": stages, "table_counts": counts,
            "panel": panel_summary, "merge_audit": panel_result["merge_audit"],
            "validation": validation, "rejected_records_by_reason_all_runs": rejections,
            "source_rejected_records": source_rejections,
            "warning_counts": warning_counts,
            "quality_metrics": quality_metrics,
            "records_read": records_read, "records_written": records_written,
            "records_rejected": records_rejected, "warnings": warning_count, "errors": 0,
        }
        if run_id:
            with connect_database(database_path) as connection:
                finish_pipeline_run(
                    connection, run_id, records_read=records_read,
                    records_written=records_written, records_rejected=records_rejected,
                )
        for reason, count in warning_counts.items():
            if count:
                logger.warning("quality_warning reason=%s affected_records=%s", reason, count)
        logger.info("pipeline_success summary=%s", json.dumps(result, default=str))
        return result
    except Exception as exc:
        logger.exception("pipeline_failed stage_orchestration_error=%s", exc)
        run_id = run_id or run_id_holder[0]
        if run_id:
            with connect_database(database_path) as connection:
                finish_pipeline_run(connection, run_id, status="failed", error_message=str(exc))
        raise
    finally:
        logger.info("pipeline_end elapsed_seconds=%.1f", time.monotonic() - wall_start)
        handler.close()
        logger.removeHandler(handler)


def _build_panel(database_path: Path, export_path: Path, report_path: Path) -> dict[str, Any]:
    with connect_database(database_path) as connection:
        return build_panel(connection, export_path=export_path, report_path=report_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-path", type=Path, default=PRODUCTION_DATABASE)
    parser.add_argument(
        "--allow-downloads", action="store_true",
        help="Permit existing source runners to acquire missing production files; cache is reused otherwise.",
    )
    args = parser.parse_args()
    try:
        result = run_pipeline(args.database_path, allow_downloads=args.allow_downloads)
    except Exception as exc:
        parser.exit(1, f"Pipeline failed: {exc}\n")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
