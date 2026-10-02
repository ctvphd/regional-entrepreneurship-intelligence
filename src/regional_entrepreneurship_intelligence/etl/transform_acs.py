"""ACS regional-control standardization and lag helpers for A4.9."""

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
    load_authoritative_reference_data,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_acs import (
    ACS_SAMPLE_PATH,
    load_acs_raw,
)


CONTROL_NAMES = {
    "population",
    "median_household_income",
    "educational_attainment_pct",
    "labor_force_participation_pct",
    "unemployment_rate",
}


@dataclass(frozen=True)
class MappingAuditSummary:
    """Coverage summary for ACS geography mapping."""

    unique_codes: int
    status_counts: dict[str, int]
    row_counts: dict[str, int]


@dataclass(frozen=True)
class ACSTransformResult:
    """Summary returned by the ACS A4.9 build."""

    pipeline_run_id: str
    staged_rows: int
    intermediate_rows: int
    rejected_rows: int
    duplicate_staging_keys: int
    duplicate_intermediate_keys: int
    missing_population_growth_rows: int
    population_growth_lag1_available: int
    income_lag1_available: int
    geography_audit: MappingAuditSummary


def build_acs_regional_controls(
    connection: sqlite3.Connection,
    *,
    load_raw_if_missing: bool = True,
) -> ACSTransformResult:
    """Build ``stg_acs`` and ``int_regional_controls`` from raw ACS rows."""
    create_schema(connection)
    load_authoritative_reference_data(connection)
    if load_raw_if_missing and connection.execute(
        "SELECT COUNT(*) FROM raw_acs;"
    ).fetchone()[0] == 0:
        load_acs_raw(connection, ACS_SAMPLE_PATH)

    run_id = start_pipeline_run(connection, stage="acs_regional_controls")
    try:
        geography_audit = audit_acs_geography(connection)
        with connection:
            connection.execute("DELETE FROM stg_acs;")
            connection.execute("DELETE FROM int_regional_controls;")
            _insert_staging_rows(connection, run_id)
            _insert_intermediate_rows(connection, run_id)
            _apply_population_growth(connection)
            _apply_control_lags(connection)
            rejected_rows = _record_exclusions(connection, run_id)
            _record_quality_metrics(connection, run_id, geography_audit)

        result = _transform_result(connection, run_id, geography_audit)
        finish_pipeline_run(
            connection,
            run_id,
            records_read=connection.execute("SELECT COUNT(*) FROM raw_acs;").fetchone()[0],
            records_written=result.intermediate_rows,
            records_rejected=rejected_rows,
        )
        return result
    except Exception as exc:
        finish_pipeline_run(connection, run_id, status="failed", error_message=str(exc))
        raise


def audit_acs_geography(connection: sqlite3.Connection) -> MappingAuditSummary:
    """Classify ACS MSA/CBSA codes against the July 2023 CBSA reference."""
    row_counts = _source_code_counts(connection)
    statuses = {
        code: classify_geography_code(connection, code) for code in sorted(row_counts)
    }
    return _summary_from_statuses(statuses, row_counts)


def classify_geography_code(connection: sqlite3.Connection, cbsa_code: str) -> str:
    """Classify one ACS CBSA code against the project geography reference."""
    direct = connection.execute(
        """
        SELECT 1
        FROM ref_geography
        WHERE cbsa_code = ?
          AND source_vintage = ?;
        """,
        (cbsa_code, GEOGRAPHY_VINTAGE),
    ).fetchone()
    if direct:
        return "direct_match"
    return "unresolved"


def compute_population_growth(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return rows with population growth using calendar-year continuity."""
    grouped = _rows_by_geography_year(rows)
    output: list[dict[str, Any]] = []
    for row in rows:
        geography_id = int(row["geography_id"])
        year = int(row["year"])
        prior = grouped[geography_id].get(year - 1)
        updated = dict(row)
        updated["population_growth"] = None
        if prior and not prior.get("has_suppression"):
            updated["population_growth"] = _growth_rate(
                updated.get("population"), prior.get("population")
            )
        output.append(updated)
    return output


def compute_lag_values(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return rows with one-year ACS control lags using calendar continuity."""
    grouped = _rows_by_geography_year(rows)
    output: list[dict[str, Any]] = []
    lag_fields = (
        ("population_growth", "population_growth_lag1"),
        ("median_household_income", "median_household_income_lag1"),
        ("educational_attainment_pct", "educational_attainment_pct_lag1"),
        ("labor_force_participation_pct", "labor_force_participation_pct_lag1"),
        ("unemployment_rate", "unemployment_rate_lag1"),
    )
    for row in rows:
        geography_id = int(row["geography_id"])
        year = int(row["year"])
        prior = grouped[geography_id].get(year - 1)
        updated = dict(row)
        for source_field, lag_field in lag_fields:
            updated[lag_field] = (
                prior.get(source_field)
                if prior and not prior.get("has_suppression")
                else None
            )
        output.append(updated)
    return output


def _insert_staging_rows(connection: sqlite3.Connection, pipeline_run_id: str) -> None:
    geographies = _geographies_by_code(connection)
    groups: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in _raw_rows(connection):
        groups.setdefault((row["source_geography_id"], row["source_year"]), []).append(row)

    for (source_geography, year), rows in sorted(groups.items()):
        geography = geographies.get(source_geography)
        status = "direct_match" if geography else "unresolved"
        by_control = {row["control_name"]: row for row in rows}
        values = {
            control: _parse_estimate(by_control.get(control)) for control in CONTROL_NAMES
        }
        moes = {
            control: _parse_moe(by_control.get(control)) for control in CONTROL_NAMES
        }
        missing = any(values[control] is None for control in CONTROL_NAMES)
        invalid_pct = _invalid_percentage_values(values)
        connection.execute(
            """
            INSERT INTO stg_acs (
                raw_acs_id,
                manifest_id,
                pipeline_run_id,
                geography_id,
                year,
                source_geography_id,
                source_geography_name,
                standardized_cbsa_code,
                standardized_cbsa_name,
                geography_mapping_status,
                population,
                population_moe,
                median_household_income,
                median_household_income_moe,
                educational_attainment_pct,
                educational_attainment_pct_moe,
                labor_force_participation_pct,
                labor_force_participation_pct_moe,
                unemployment_rate,
                unemployment_rate_moe,
                is_missing,
                is_suppressed,
                source_raw_acs_ids,
                notes
            )
            VALUES (
                NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, 0, ?, ?
            );
            """,
            (
                rows[0]["manifest_id"],
                pipeline_run_id,
                geography[0] if geography else None,
                year,
                source_geography,
                rows[0]["source_geography_name"],
                geography[1] if geography else None,
                geography[2] if geography else None,
                status,
                values["population"],
                moes["population"],
                values["median_household_income"],
                moes["median_household_income"],
                values["educational_attainment_pct"],
                moes["educational_attainment_pct"],
                values["labor_force_participation_pct"],
                moes["labor_force_participation_pct"],
                values["unemployment_rate"],
                moes["unemployment_rate"],
                1 if missing or invalid_pct else 0,
                json.dumps(sorted(row["raw_acs_id"] for row in rows)),
                (
                    "ACS 5-year profile MSA-year controls; income is source-reported "
                    "ACS vintage dollars and is not additionally deflated in A4.9."
                ),
            ),
        )


def _insert_intermediate_rows(connection: sqlite3.Connection, pipeline_run_id: str) -> None:
    staged = connection.execute(
        """
        SELECT geography_id,
               year,
               standardized_cbsa_code,
               standardized_cbsa_name,
               population,
               median_household_income,
               educational_attainment_pct,
               labor_force_participation_pct,
               unemployment_rate,
               geography_mapping_status,
               is_suppressed,
               manifest_id
        FROM stg_acs
        WHERE geography_mapping_status = 'direct_match'
          AND is_missing = 0;
        """
    ).fetchall()
    for row in staged:
        connection.execute(
            """
            INSERT INTO int_regional_controls (
                geography_id,
                year,
                standardized_cbsa_code,
                standardized_cbsa_name,
                population,
                population_growth,
                median_household_income,
                educational_attainment_pct,
                labor_force_participation_pct,
                unemployment_rate,
                population_growth_lag1,
                median_household_income_lag1,
                educational_attainment_pct_lag1,
                labor_force_participation_pct_lag1,
                unemployment_rate_lag1,
                geography_mapping_status,
                has_suppression,
                source_manifest_id,
                pipeline_run_id,
                notes
            )
            VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, ?, ?, ?, ?, ?);
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
                row[8],
                row[9],
                row[10] or 0,
                row[11],
                pipeline_run_id,
                "A4.9 ACS regional-control record; no industry duplication or source integration.",
            ),
        )


def _apply_population_growth(connection: sqlite3.Connection) -> None:
    for row in compute_population_growth(_intermediate_rows(connection)):
        connection.execute(
            """
            UPDATE int_regional_controls
            SET population_growth = ?
            WHERE geography_id = ?
              AND year = ?;
            """,
            (row["population_growth"], row["geography_id"], row["year"]),
        )


def _apply_control_lags(connection: sqlite3.Connection) -> None:
    for row in compute_lag_values(_intermediate_rows(connection)):
        connection.execute(
            """
            UPDATE int_regional_controls
            SET population_growth_lag1 = ?,
                median_household_income_lag1 = ?,
                educational_attainment_pct_lag1 = ?,
                labor_force_participation_pct_lag1 = ?,
                unemployment_rate_lag1 = ?
            WHERE geography_id = ?
              AND year = ?;
            """,
            (
                row["population_growth_lag1"],
                row["median_household_income_lag1"],
                row["educational_attainment_pct_lag1"],
                row["labor_force_participation_pct_lag1"],
                row["unemployment_rate_lag1"],
                row["geography_id"],
                row["year"],
            ),
        )


def _record_exclusions(connection: sqlite3.Connection, pipeline_run_id: str) -> int:
    excluded = connection.execute(
        """
        SELECT source_geography_id,
               source_geography_name,
               year,
               geography_mapping_status,
               is_missing,
               population,
               educational_attainment_pct,
               labor_force_participation_pct,
               unemployment_rate
        FROM stg_acs
        WHERE geography_mapping_status <> 'direct_match'
           OR is_missing = 1;
        """
    ).fetchall()
    count = 0
    for row in excluded:
        reason = "missing_required_field"
        if row[3] != "direct_match":
            reason = "unresolved_geography"
        elif any(value is not None and not 0 <= value <= 100 for value in row[6:9]):
            reason = "invalid_numeric_value"
        insert_rejected_record(
            connection,
            pipeline_run_id=pipeline_run_id,
            table_name="stg_acs",
            stage="acs_regional_controls",
            reason_code=reason,
            source_row_identifier=f"year={row[2]}|geo={row[0]}",
            reason_detail="Record retained in staging but excluded from int_regional_controls.",
            serialized_record={
                "source_geography_id": row[0],
                "source_geography_name": row[1],
                "year": row[2],
                "geography_mapping_status": row[3],
                "is_missing": row[4],
            },
        )
        count += 1
    return count


def _record_quality_metrics(
    connection: sqlite3.Connection,
    pipeline_run_id: str,
    geography_audit: MappingAuditSummary,
) -> None:
    metrics = {
        "raw_acs_rows": connection.execute("SELECT COUNT(*) FROM raw_acs;").fetchone()[0],
        "stg_acs_rows": connection.execute("SELECT COUNT(*) FROM stg_acs;").fetchone()[0],
        "int_regional_controls_rows": connection.execute(
            "SELECT COUNT(*) FROM int_regional_controls;"
        ).fetchone()[0],
        "unique_msas": connection.execute(
            "SELECT COUNT(DISTINCT geography_id) FROM int_regional_controls;"
        ).fetchone()[0],
        "year_coverage": connection.execute(
            "SELECT COUNT(DISTINCT year) FROM int_regional_controls;"
        ).fetchone()[0],
        "unresolved_geography_rows": geography_audit.row_counts.get("unresolved", 0),
        "duplicate_staging_keys": _duplicate_staging_keys(connection),
        "duplicate_intermediate_keys": _duplicate_intermediate_keys(connection),
        "missing_population_rows": connection.execute(
            "SELECT COUNT(*) FROM stg_acs WHERE population IS NULL;"
        ).fetchone()[0],
        "missing_income_rows": connection.execute(
            "SELECT COUNT(*) FROM stg_acs WHERE median_household_income IS NULL;"
        ).fetchone()[0],
        "invalid_percentage_rows": connection.execute(
            """
            SELECT COUNT(*)
            FROM stg_acs
            WHERE educational_attainment_pct NOT BETWEEN 0 AND 100
               OR labor_force_participation_pct NOT BETWEEN 0 AND 100
               OR unemployment_rate NOT BETWEEN 0 AND 100;
            """
        ).fetchone()[0],
        "population_growth_missing_rows": connection.execute(
            "SELECT COUNT(*) FROM int_regional_controls WHERE population_growth IS NULL;"
        ).fetchone()[0],
        "lag1_missing_rows": connection.execute(
            "SELECT COUNT(*) FROM int_regional_controls WHERE median_household_income_lag1 IS NULL;"
        ).fetchone()[0],
        "rejected_rows": connection.execute(
            "SELECT COUNT(*) FROM quality_rejected_record WHERE pipeline_run_id = ?;",
            (pipeline_run_id,),
        ).fetchone()[0],
    }
    for name, value in metrics.items():
        insert_quality_metric(
            connection,
            pipeline_run_id=pipeline_run_id,
            table_name="acs_a49",
            metric_name=name,
            metric_value=float(value),
            scope="A4.9 ACS regional controls",
        )


def _transform_result(
    connection: sqlite3.Connection,
    pipeline_run_id: str,
    geography_audit: MappingAuditSummary,
) -> ACSTransformResult:
    return ACSTransformResult(
        pipeline_run_id=pipeline_run_id,
        staged_rows=connection.execute("SELECT COUNT(*) FROM stg_acs;").fetchone()[0],
        intermediate_rows=connection.execute(
            "SELECT COUNT(*) FROM int_regional_controls;"
        ).fetchone()[0],
        rejected_rows=connection.execute(
            "SELECT COUNT(*) FROM quality_rejected_record WHERE pipeline_run_id = ?;",
            (pipeline_run_id,),
        ).fetchone()[0],
        duplicate_staging_keys=_duplicate_staging_keys(connection),
        duplicate_intermediate_keys=_duplicate_intermediate_keys(connection),
        missing_population_growth_rows=connection.execute(
            "SELECT COUNT(*) FROM int_regional_controls WHERE population_growth IS NULL;"
        ).fetchone()[0],
        population_growth_lag1_available=connection.execute(
            "SELECT COUNT(*) FROM int_regional_controls WHERE population_growth_lag1 IS NOT NULL;"
        ).fetchone()[0],
        income_lag1_available=connection.execute(
            "SELECT COUNT(*) FROM int_regional_controls WHERE median_household_income_lag1 IS NOT NULL;"
        ).fetchone()[0],
        geography_audit=geography_audit,
    )


def _raw_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        {
            "raw_acs_id": row[0],
            "manifest_id": row[1],
            "source_year": row[2],
            "source_geography_id": row[3],
            "source_geography_name": row[4],
            "source_variable_id": row[5],
            "source_moe_variable_id": row[6],
            "source_product": row[7],
            "control_name": row[8],
            "estimate_value": row[9],
            "margin_of_error": row[10],
            "source_row_identifier": row[11],
            "raw_payload": row[12],
        }
        for row in connection.execute(
            """
            SELECT raw_acs_id,
                   manifest_id,
                   source_year,
                   source_geography_id,
                   source_geography_name,
                   source_variable_id,
                   source_moe_variable_id,
                   source_product,
                   control_name,
                   estimate_value,
                   margin_of_error,
                   source_row_identifier,
                   raw_payload
            FROM raw_acs
            WHERE source_year BETWEEN 2010 AND 2023;
            """
        )
    ]


def _parse_estimate(row: dict[str, Any] | None) -> float | None:
    if row is None:
        return None
    return _to_float(row.get("estimate_value"))


def _parse_moe(row: dict[str, Any] | None) -> float | None:
    if row is None:
        return None
    value = _to_float(row.get("margin_of_error"))
    if value is None or value < 0:
        return None
    return value


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text in {"", "-666666666", "-999999999", "-888888888", "-222222222"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _growth_rate(current: float | None, prior: float | None) -> float | None:
    if current is None or prior is None or prior <= 0:
        return None
    return (current - prior) / prior


def _invalid_percentage_values(values: dict[str, float | None]) -> bool:
    for field in (
        "educational_attainment_pct",
        "labor_force_participation_pct",
        "unemployment_rate",
    ):
        value = values.get(field)
        if value is not None and not 0 <= value <= 100:
            return True
    return False


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


def _source_code_counts(connection: sqlite3.Connection) -> dict[str, int]:
    rows = connection.execute(
        """
        SELECT source_geography_id, COUNT(*)
        FROM raw_acs
        WHERE source_year BETWEEN 2010 AND 2023
        GROUP BY source_geography_id;
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


def _intermediate_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        {
            "geography_id": row[0],
            "year": row[1],
            "population": row[2],
            "population_growth": row[3],
            "median_household_income": row[4],
            "educational_attainment_pct": row[5],
            "labor_force_participation_pct": row[6],
            "unemployment_rate": row[7],
            "has_suppression": bool(row[8]),
        }
        for row in connection.execute(
            """
            SELECT geography_id,
                   year,
                   population,
                   population_growth,
                   median_household_income,
                   educational_attainment_pct,
                   labor_force_participation_pct,
                   unemployment_rate,
                   has_suppression
            FROM int_regional_controls
            ORDER BY geography_id, year;
            """
        )
    ]


def _rows_by_geography_year(
    rows: list[dict[str, Any]]
) -> dict[int, dict[int, dict[str, Any]]]:
    grouped: dict[int, dict[int, dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(int(row["geography_id"]), {})[int(row["year"])] = row
    return grouped


def _duplicate_staging_keys(connection: sqlite3.Connection) -> int:
    return connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT geography_id, year, COUNT(*) AS c
            FROM stg_acs
            GROUP BY geography_id, year
            HAVING c > 1
        );
        """
    ).fetchone()[0]


def _duplicate_intermediate_keys(connection: sqlite3.Connection) -> int:
    return connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT geography_id, year, COUNT(*) AS c
            FROM int_regional_controls
            GROUP BY geography_id, year
            HAVING c > 1
        );
        """
    ).fetchone()[0]


def main() -> None:
    """CLI entry point for the A4.9 ACS transformation."""
    parser = argparse.ArgumentParser(
        description="Build ACS staging and regional-control layers."
    )
    parser.add_argument(
        "--database-path",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the SQLite database file.",
    )
    args = parser.parse_args()
    with connect_database(args.database_path) as connection:
        result = build_acs_regional_controls(connection)
    print(
        "Built ACS regional-control layers: "
        f"stg_acs={result.staged_rows}, "
        f"int_regional_controls={result.intermediate_rows}, "
        f"population_growth_missing={result.missing_population_growth_rows}, "
        f"income_lag1={result.income_lag1_available}, "
        f"rejected={result.rejected_rows}"
    )


if __name__ == "__main__":
    main()
