"""BDS standardization, startup construction, and lag helpers for A4.6."""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from regional_entrepreneurship_intelligence.database.connection import (
    DEFAULT_DATABASE_PATH,
    connect_database,
)
from regional_entrepreneurship_intelligence.database.metadata import (
    finish_pipeline_run,
    insert_quality_metric,
    insert_rejected_record,
    start_pipeline_run,
)
from regional_entrepreneurship_intelligence.database.reference import (
    GEOGRAPHY_VINTAGE,
    NAICS_ANALYTICAL_VERSION,
    load_authoritative_reference_data,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_bds import (
    BDS_FIRM_AGE_SAMPLE_PATH,
    BDS_SAMPLE_PATH,
    load_bds_firm_age_raw,
    load_bds_raw,
)


AGE0_CATEGORY = "a) 0"


@dataclass(frozen=True)
class MappingAuditSummary:
    """Coverage summary for geography or industry mapping."""

    unique_codes: int
    status_counts: dict[str, int]
    row_counts: dict[str, int]


@dataclass(frozen=True)
class BDSTransformResult:
    """Summary returned by the BDS A4.6 build."""

    pipeline_run_id: str
    staged_rows: int
    intermediate_rows: int
    rejected_rows: int
    duplicate_staging_keys: int
    duplicate_intermediate_keys: int
    lag1_available: int
    lag2_available: int
    lag3_available: int
    suppressed_staging_rows: int
    missing_startup_measure_rows: int
    geography_audit: MappingAuditSummary
    industry_audit: MappingAuditSummary


def build_bds_standardized_layers(
    connection: sqlite3.Connection,
    *,
    load_raw_if_missing: bool = True,
) -> BDSTransformResult:
    """Build ``stg_bds`` and ``int_entrepreneurship`` from raw BDS sample rows."""
    create_schema(connection)
    load_authoritative_reference_data(connection)
    if load_raw_if_missing:
        if connection.execute("SELECT COUNT(*) FROM raw_bds;").fetchone()[0] == 0:
            load_bds_raw(connection, BDS_SAMPLE_PATH)
        if connection.execute("SELECT COUNT(*) FROM raw_bds_firm_age;").fetchone()[0] == 0:
            load_bds_firm_age_raw(connection, BDS_FIRM_AGE_SAMPLE_PATH)

    run_id = start_pipeline_run(connection, stage="bds_standardization")
    try:
        geography_audit = audit_bds_geography(connection)
        industry_audit = audit_bds_industry(connection)
        with connection:
            connection.execute("DELETE FROM stg_bds;")
            connection.execute("DELETE FROM int_entrepreneurship;")
            _insert_staging_rows(connection, run_id)
            _insert_intermediate_rows(connection, run_id)
            _apply_startup_rate_lags(connection)
            rejected_rows = _record_exclusions(connection, run_id)
            _record_quality_metrics(connection, run_id, geography_audit, industry_audit)

        result = _transform_result(connection, run_id, geography_audit, industry_audit)
        finish_pipeline_run(
            connection,
            run_id,
            records_read=connection.execute(
                "SELECT COUNT(*) FROM raw_bds_firm_age;"
            ).fetchone()[0],
            records_written=result.intermediate_rows,
            records_rejected=rejected_rows,
        )
        return result
    except Exception as exc:
        finish_pipeline_run(connection, run_id, status="failed", error_message=str(exc))
        raise


def audit_bds_geography(connection: sqlite3.Connection) -> MappingAuditSummary:
    """Classify BDS native MSA codes against the July 2023 CBSA reference."""
    row_counts = _source_code_counts(connection, "source_geography_id")
    statuses = {
        code: classify_geography_code(connection, code) for code in sorted(row_counts)
    }
    return _summary_from_statuses(statuses, row_counts)


def classify_geography_code(connection: sqlite3.Connection, msa_code: str) -> str:
    """Classify one BDS MSA code against the project geography reference."""
    direct = connection.execute(
        """
        SELECT 1
        FROM ref_geography
        WHERE cbsa_code = ?
          AND source_vintage = ?;
        """,
        (msa_code, GEOGRAPHY_VINTAGE),
    ).fetchone()
    if direct:
        return "direct_match"
    return "unresolved"


def audit_bds_industry(connection: sqlite3.Connection) -> MappingAuditSummary:
    """Classify BDS 2017 sector codes against the 2022 NAICS reference."""
    row_counts = _source_code_counts(connection, "source_industry_id")
    statuses = {
        code: classify_industry_code(connection, code) for code in sorted(row_counts)
    }
    return _summary_from_statuses(statuses, row_counts)


def classify_industry_code(connection: sqlite3.Connection, sector_code: str) -> str:
    """Classify one BDS sector code using exact 2022 NAICS sector evidence."""
    exact = connection.execute(
        """
        SELECT 1
        FROM ref_industry
        WHERE naics_code = ?
          AND naics_version = ?
          AND naics_level = 2;
        """,
        (sector_code, NAICS_ANALYTICAL_VERSION),
    ).fetchone()
    if exact:
        return "directly_comparable"
    return "unresolved"


def compute_lag_values(
    rows: list[dict[str, Any]], lag_years: tuple[int, ...] = (1, 2, 3)
) -> list[dict[str, Any]]:
    """Return rows with calendar-year lag values within geography/industry groups."""
    grouped: dict[tuple[int, int], dict[int, dict[str, Any]]] = {}
    for row in rows:
        key = (int(row["geography_id"]), int(row["industry_id"]))
        grouped.setdefault(key, {})[int(row["year"])] = row

    output: list[dict[str, Any]] = []
    for row in rows:
        key = (int(row["geography_id"]), int(row["industry_id"]))
        year = int(row["year"])
        updated = dict(row)
        for lag in lag_years:
            prior = grouped[key].get(year - lag)
            value = None
            if prior and not prior.get("has_suppression"):
                value = prior.get("startup_rate")
            updated[f"startup_rate_lag{lag}"] = value
        output.append(updated)
    return output


def _insert_staging_rows(connection: sqlite3.Connection, pipeline_run_id: str) -> None:
    backbone = _raw_backbone_by_key(connection)
    geographies = _geographies_by_code(connection)
    industries = _industries_by_code(connection)
    firm_age_rows = connection.execute(
        """
        SELECT raw_bds_firm_age_id,
               manifest_id,
               source_year,
               source_geography_id,
               source_industry_id,
               source_fagecoarse,
               raw_payload
        FROM raw_bds_firm_age
        WHERE source_year BETWEEN 2010 AND 2023
          AND source_fagecoarse = ?;
        """,
        (AGE0_CATEGORY,),
    ).fetchall()
    for row in firm_age_rows:
        (
            raw_id,
            manifest_id,
            year,
            source_geography,
            source_industry,
            fagecoarse,
            payload_json,
        ) = row
        payload = json.loads(payload_json)
        backbone_payload = backbone.get((year, source_geography, source_industry), {})
        geography = geographies.get(source_geography)
        industry = industries.get(source_industry)
        geography_status = "direct_match" if geography else "unresolved"
        industry_status = "directly_comparable" if industry else "unresolved"
        startup_count = _to_float(payload.get("firms"))
        startup_job_creation = _to_float(payload.get("job_creation"))
        denominator = _to_float(backbone_payload.get("firms"))
        startup_rate = (
            (startup_count / denominator) * 100
            if startup_count is not None and denominator and denominator > 0
            else None
        )
        establishment_entry = _to_float(backbone_payload.get("estabs_entry"))
        establishment_entry_rate = _to_float(backbone_payload.get("estabs_entry_rate"))
        suppressed = (
            payload.get("firms") in {"D", "S"}
            or backbone_payload.get("firms") in {"D", "S"}
        )
        missing = startup_count is None or startup_rate is None
        connection.execute(
            """
            INSERT INTO stg_bds (
                raw_bds_id,
                manifest_id,
                pipeline_run_id,
                geography_id,
                industry_id,
                year,
                source_geography_id,
                source_industry_id,
                source_fagecoarse,
                standardized_cbsa_code,
                standardized_cbsa_name,
                standardized_sector_code,
                geography_mapping_status,
                industry_mapping_status,
                firm_startups,
                startup_rate,
                establishment_entry,
                establishment_entry_rate,
                startup_job_creation,
                is_missing,
                is_suppressed,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                None,
                manifest_id,
                pipeline_run_id,
                geography[0] if geography else None,
                industry[0] if industry else None,
                year,
                source_geography,
                source_industry,
                fagecoarse,
                geography[1] if geography else None,
                geography[2] if geography else None,
                industry[1] if industry else None,
                geography_status,
                industry_status,
                startup_count,
                startup_rate,
                establishment_entry,
                establishment_entry_rate,
                startup_job_creation,
                1 if missing else 0,
                1 if suppressed else 0,
                (
                    "Startup count uses BDS firm-age-coarse age 0 firms; "
                    "startup rate uses age-0 firms divided by all BDS firms "
                    "in the same MSA-sector-year."
                ),
            ),
        )


def _insert_intermediate_rows(connection: sqlite3.Connection, pipeline_run_id: str) -> None:
    staged = connection.execute(
        """
        SELECT geography_id,
               industry_id,
               year,
               firm_startups,
               startup_rate,
               establishment_entry,
               establishment_entry_rate,
               startup_job_creation,
               is_suppressed,
               manifest_id,
               geography_mapping_status,
               industry_mapping_status
        FROM stg_bds
        WHERE geography_mapping_status = 'direct_match'
          AND industry_mapping_status = 'directly_comparable'
          AND firm_startups IS NOT NULL
          AND startup_rate IS NOT NULL
          AND is_suppressed = 0;
        """
    ).fetchall()
    for row in staged:
        connection.execute(
            """
            INSERT INTO int_entrepreneurship (
                geography_id,
                industry_id,
                year,
                firm_startups,
                startup_rate,
                establishment_entry,
                establishment_entry_rate,
                startup_job_creation,
                startup_rate_lag1,
                startup_rate_lag2,
                startup_rate_lag3,
                lagged_startup_rate,
                geography_mapping_status,
                industry_mapping_status,
                has_suppression,
                source_manifest_id,
                pipeline_run_id,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, ?, ?, ?, ?, ?, ?);
            """,
            (
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                row[6],
                row[7],
                row[10],
                row[11],
                row[8] or 0,
                row[9],
                pipeline_run_id,
                "A4.6 BDS standardized entrepreneurship record; no target created.",
            ),
        )


def _apply_startup_rate_lags(connection: sqlite3.Connection) -> None:
    rows = [
        {
            "geography_id": row[0],
            "industry_id": row[1],
            "year": row[2],
            "startup_rate": row[3],
            "has_suppression": bool(row[4]),
        }
        for row in connection.execute(
            """
            SELECT geography_id, industry_id, year, startup_rate, has_suppression
            FROM int_entrepreneurship
            ORDER BY geography_id, industry_id, year;
            """
        )
    ]
    lagged = compute_lag_values(rows)
    for row in lagged:
        connection.execute(
            """
            UPDATE int_entrepreneurship
            SET startup_rate_lag1 = ?,
                startup_rate_lag2 = ?,
                startup_rate_lag3 = ?,
                lagged_startup_rate = ?
            WHERE geography_id = ?
              AND industry_id = ?
              AND year = ?;
            """,
            (
                row["startup_rate_lag1"],
                row["startup_rate_lag2"],
                row["startup_rate_lag3"],
                row["startup_rate_lag1"],
                row["geography_id"],
                row["industry_id"],
                row["year"],
            ),
        )


def _record_exclusions(connection: sqlite3.Connection, pipeline_run_id: str) -> int:
    excluded = connection.execute(
        """
        SELECT source_geography_id,
               source_industry_id,
               year,
               geography_mapping_status,
               industry_mapping_status,
               is_missing,
               is_suppressed,
               notes
        FROM stg_bds
        WHERE geography_mapping_status <> 'direct_match'
           OR industry_mapping_status <> 'directly_comparable'
           OR startup_rate IS NULL
           OR is_suppressed = 1;
        """
    ).fetchall()
    count = 0
    for row in excluded:
        reason = "missing_required_startup_measure"
        if row[3] != "direct_match":
            reason = "unresolved_geography"
        elif row[4] != "directly_comparable":
            reason = "unresolved_industry"
        elif row[6]:
            reason = "suppressed_value"
        insert_rejected_record(
            connection,
            pipeline_run_id=pipeline_run_id,
            table_name="stg_bds",
            stage="bds_standardization",
            reason_code=reason,
            source_row_identifier=(
                f"year={row[2]}|msa={row[0]}|sector={row[1]}|fagecoarse={AGE0_CATEGORY}"
            ),
            reason_detail="Record retained in staging but excluded from int_entrepreneurship.",
            serialized_record={
                "source_geography_id": row[0],
                "source_industry_id": row[1],
                "year": row[2],
                "geography_mapping_status": row[3],
                "industry_mapping_status": row[4],
                "is_missing": row[5],
                "is_suppressed": row[6],
            },
        )
        count += 1
    return count


def _record_quality_metrics(
    connection: sqlite3.Connection,
    pipeline_run_id: str,
    geography_audit: MappingAuditSummary,
    industry_audit: MappingAuditSummary,
) -> None:
    metrics = {
        "raw_bds_rows": connection.execute("SELECT COUNT(*) FROM raw_bds;").fetchone()[0],
        "raw_bds_firm_age_rows": connection.execute(
            "SELECT COUNT(*) FROM raw_bds_firm_age;"
        ).fetchone()[0],
        "raw_bds_suppressed_rows": connection.execute(
            "SELECT COUNT(*) FROM raw_bds WHERE is_suppressed = 1;"
        ).fetchone()[0],
        "raw_bds_firm_age_suppressed_rows": connection.execute(
            "SELECT COUNT(*) FROM raw_bds_firm_age WHERE is_suppressed = 1;"
        ).fetchone()[0],
        "stg_bds_rows": connection.execute("SELECT COUNT(*) FROM stg_bds;").fetchone()[0],
        "int_entrepreneurship_rows": connection.execute(
            "SELECT COUNT(*) FROM int_entrepreneurship;"
        ).fetchone()[0],
        "unresolved_geography_rows": geography_audit.row_counts.get("unresolved", 0),
        "unresolved_industry_rows": industry_audit.row_counts.get("unresolved", 0),
        "suppressed_stg_bds_rows": connection.execute(
            "SELECT COUNT(*) FROM stg_bds WHERE is_suppressed = 1;"
        ).fetchone()[0],
        "missing_startup_measure_rows": connection.execute(
            "SELECT COUNT(*) FROM stg_bds WHERE startup_rate IS NULL;"
        ).fetchone()[0],
        "duplicate_staging_keys": _duplicate_staging_keys(connection),
        "duplicate_intermediate_keys": _duplicate_intermediate_keys(connection),
        "lag1_missing_rows": connection.execute(
            "SELECT COUNT(*) FROM int_entrepreneurship WHERE startup_rate_lag1 IS NULL;"
        ).fetchone()[0],
        "lag2_missing_rows": connection.execute(
            "SELECT COUNT(*) FROM int_entrepreneurship WHERE startup_rate_lag2 IS NULL;"
        ).fetchone()[0],
        "lag3_missing_rows": connection.execute(
            "SELECT COUNT(*) FROM int_entrepreneurship WHERE startup_rate_lag3 IS NULL;"
        ).fetchone()[0],
        "year_coverage_count": connection.execute(
            "SELECT COUNT(DISTINCT year) FROM int_entrepreneurship;"
        ).fetchone()[0],
        "rejected_rows": connection.execute(
            "SELECT COUNT(*) FROM quality_rejected_record WHERE pipeline_run_id = ?;",
            (pipeline_run_id,),
        ).fetchone()[0],
        "valid_msa_sector_panels": connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT geography_id, industry_id
                FROM int_entrepreneurship
                GROUP BY geography_id, industry_id
            );
            """
        ).fetchone()[0],
        "balanced_msa_sector_panels": connection.execute(
            """SELECT COUNT(*) FROM (
                   SELECT geography_id, industry_id
                   FROM int_entrepreneurship
                   GROUP BY geography_id, industry_id
                   HAVING COUNT(DISTINCT year) = 14
               );"""
        ).fetchone()[0],
    }
    for name, value in metrics.items():
        insert_quality_metric(
            connection,
            pipeline_run_id=pipeline_run_id,
            table_name="bds_a46",
            metric_name=name,
            metric_value=float(value),
            scope="BDS standardization",
        )


def _transform_result(
    connection: sqlite3.Connection,
    pipeline_run_id: str,
    geography_audit: MappingAuditSummary,
    industry_audit: MappingAuditSummary,
) -> BDSTransformResult:
    return BDSTransformResult(
        pipeline_run_id=pipeline_run_id,
        staged_rows=connection.execute("SELECT COUNT(*) FROM stg_bds;").fetchone()[0],
        intermediate_rows=connection.execute(
            "SELECT COUNT(*) FROM int_entrepreneurship;"
        ).fetchone()[0],
        rejected_rows=connection.execute(
            "SELECT COUNT(*) FROM quality_rejected_record WHERE pipeline_run_id = ?;",
            (pipeline_run_id,),
        ).fetchone()[0],
        duplicate_staging_keys=_duplicate_staging_keys(connection),
        duplicate_intermediate_keys=_duplicate_intermediate_keys(connection),
        lag1_available=connection.execute(
            "SELECT COUNT(*) FROM int_entrepreneurship WHERE startup_rate_lag1 IS NOT NULL;"
        ).fetchone()[0],
        lag2_available=connection.execute(
            "SELECT COUNT(*) FROM int_entrepreneurship WHERE startup_rate_lag2 IS NOT NULL;"
        ).fetchone()[0],
        lag3_available=connection.execute(
            "SELECT COUNT(*) FROM int_entrepreneurship WHERE startup_rate_lag3 IS NOT NULL;"
        ).fetchone()[0],
        suppressed_staging_rows=connection.execute(
            "SELECT COUNT(*) FROM stg_bds WHERE is_suppressed = 1;"
        ).fetchone()[0],
        missing_startup_measure_rows=connection.execute(
            "SELECT COUNT(*) FROM stg_bds WHERE startup_rate IS NULL;"
        ).fetchone()[0],
        geography_audit=geography_audit,
        industry_audit=industry_audit,
    )


def _source_code_counts(connection: sqlite3.Connection, column: str) -> dict[str, int]:
    rows = connection.execute(
        f"""
        SELECT {column}, COUNT(*)
        FROM (
            SELECT {column}, source_year FROM raw_bds
            UNION ALL
            SELECT {column}, source_year FROM raw_bds_firm_age
        )
        WHERE source_year BETWEEN 2010 AND 2023
        GROUP BY {column};
        """
    ).fetchall()
    return {row[0]: int(row[1]) for row in rows}


def _summary_from_statuses(
    statuses: dict[str, str], row_counts: dict[str, int]
) -> MappingAuditSummary:
    status_counts: dict[str, int] = {}
    rows_by_status: dict[str, int] = {}
    for code, status in statuses.items():
        status_counts[status] = status_counts.get(status, 0) + 1
        rows_by_status[status] = rows_by_status.get(status, 0) + row_counts[code]
    return MappingAuditSummary(
        unique_codes=len(statuses),
        status_counts=status_counts,
        row_counts=rows_by_status,
    )


def _raw_backbone_by_key(connection: sqlite3.Connection) -> dict[tuple[int, str, str], dict[str, str]]:
    rows = connection.execute(
        """
        SELECT source_year, source_geography_id, source_industry_id, raw_payload
        FROM raw_bds
        WHERE source_year BETWEEN 2010 AND 2023;
        """
    ).fetchall()
    return {
        (row[0], row[1], row[2]): json.loads(row[3])
        for row in rows
    }


def _geographies_by_code(connection: sqlite3.Connection) -> dict[str, tuple[int, str, str]]:
    return {
        row[0]: (row[1], row[0], row[2])
        for row in connection.execute(
            """
            SELECT cbsa_code, geography_id, cbsa_name
            FROM ref_geography
            WHERE source_vintage = ?;
            """,
            (GEOGRAPHY_VINTAGE,),
        )
    }


def _industries_by_code(connection: sqlite3.Connection) -> dict[str, tuple[int, str]]:
    return {
        row[0]: (row[1], row[0])
        for row in connection.execute(
            """
            SELECT naics_code, industry_id
            FROM ref_industry
            WHERE naics_version = ?
              AND naics_level = 2;
            """,
            (NAICS_ANALYTICAL_VERSION,),
        )
    }


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text in {"", "D", "N", "S", "X"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _duplicate_staging_keys(connection: sqlite3.Connection) -> int:
    return connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT source_geography_id, source_industry_id, year, source_fagecoarse, COUNT(*) AS c
            FROM stg_bds
            GROUP BY source_geography_id, source_industry_id, year, source_fagecoarse
            HAVING c > 1
        );
        """
    ).fetchone()[0]


def _duplicate_intermediate_keys(connection: sqlite3.Connection) -> int:
    return connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT geography_id, industry_id, year, COUNT(*) AS c
            FROM int_entrepreneurship
            GROUP BY geography_id, industry_id, year
            HAVING c > 1
        );
        """
    ).fetchone()[0]


def main() -> None:
    """CLI entry point for the A4.6 BDS transformation."""
    parser = argparse.ArgumentParser(
        description="Build BDS staging and entrepreneurship layers."
    )
    parser.add_argument(
        "--database-path",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the SQLite database file.",
    )
    args = parser.parse_args()
    with connect_database(args.database_path) as connection:
        result = build_bds_standardized_layers(connection)
    print(
        "Built BDS standardized layers: "
        f"stg_bds={result.staged_rows}, "
        f"int_entrepreneurship={result.intermediate_rows}, "
        f"lag1={result.lag1_available}, "
        f"lag2={result.lag2_available}, "
        f"lag3={result.lag3_available}, "
        f"rejected={result.rejected_rows}"
    )


if __name__ == "__main__":
    main()
