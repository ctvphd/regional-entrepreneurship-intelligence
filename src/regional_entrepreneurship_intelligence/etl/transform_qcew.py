"""QCEW standardization, industry-growth, and lag helpers for A4.8."""

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
from regional_entrepreneurship_intelligence.database.naics_versions import (
    classify_sector, source_year_naics,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_qcew import (
    QCEW_SAMPLE_PATH,
    load_qcew_raw,
)


PRIVATE_OWNERSHIP_CODE = "5"
OWNERSHIP_SCOPE = "private_ownership"
VALID_GEOGRAPHY_STATUS = "crosswalk_required"
VALID_INDUSTRY_STATUS = "directly_comparable"


@dataclass(frozen=True)
class MappingAuditSummary:
    """Coverage summary for geography or industry mapping."""

    unique_codes: int
    status_counts: dict[str, int]
    row_counts: dict[str, int]


@dataclass(frozen=True)
class QCEWTransformResult:
    """Summary returned by the QCEW A4.8 build."""

    pipeline_run_id: str
    staged_rows: int
    intermediate_rows: int
    rejected_rows: int
    duplicate_staging_keys: int
    duplicate_intermediate_keys: int
    suppressed_staging_rows: int
    incomplete_aggregation_rows: int
    missing_growth_rows: int
    employment_growth_lag1_available: int
    employment_growth_lag2_available: int
    employment_growth_lag3_available: int
    establishment_growth_lag1_available: int
    establishment_growth_lag2_available: int
    establishment_growth_lag3_available: int
    geography_audit: MappingAuditSummary
    industry_audit: MappingAuditSummary


def build_qcew_standardized_layers(
    connection: sqlite3.Connection,
    *,
    load_raw_if_missing: bool = True,
) -> QCEWTransformResult:
    """Build ``stg_qcew`` and ``int_industry_growth`` from raw QCEW rows."""
    create_schema(connection)
    load_authoritative_reference_data(connection)
    if load_raw_if_missing and connection.execute(
        "SELECT COUNT(*) FROM raw_qcew;"
    ).fetchone()[0] == 0:
        load_qcew_raw(connection, QCEW_SAMPLE_PATH)

    run_id = start_pipeline_run(connection, stage="qcew_standardization")
    try:
        geography_audit = audit_qcew_geography(connection)
        industry_audit = audit_qcew_industry(connection)
        with connection:
            connection.execute("DELETE FROM stg_qcew;")
            connection.execute("DELETE FROM int_industry_growth;")
            _insert_staging_rows(connection, run_id)
            _insert_intermediate_rows(connection, run_id)
            _apply_growth_rates(connection)
            _apply_growth_lags(connection)
            rejected_rows = _record_exclusions(connection, run_id)
            _record_quality_metrics(connection, run_id, geography_audit, industry_audit)

        result = _transform_result(connection, run_id, geography_audit, industry_audit)
        finish_pipeline_run(
            connection,
            run_id,
            records_read=connection.execute("SELECT COUNT(*) FROM raw_qcew;").fetchone()[0],
            records_written=result.intermediate_rows,
            records_rejected=rejected_rows,
        )
        return result
    except Exception as exc:
        finish_pipeline_run(connection, run_id, status="failed", error_message=str(exc))
        raise


def audit_qcew_geography(connection: sqlite3.Connection) -> MappingAuditSummary:
    """Classify QCEW area codes against the July 2023 CBSA framework."""
    row_counts = _source_code_counts(connection, "source_geography_id")
    statuses = {
        code: classify_geography_code(connection, code) for code in sorted(row_counts)
    }
    return _summary_from_statuses(statuses, row_counts)


def classify_geography_code(connection: sqlite3.Connection, area_fips: str) -> str:
    """Classify one QCEW area code for the selected county-aggregation strategy."""
    if _county_crosswalk_record(connection, area_fips):
        return "crosswalk_required"
    direct = connection.execute(
        """
        SELECT 1
        FROM ref_geography
        WHERE cbsa_code = ?
          AND source_vintage = ?;
        """,
        (area_fips, GEOGRAPHY_VINTAGE),
    ).fetchone()
    if direct:
        return "direct_match"
    return "unresolved"


def audit_qcew_industry(connection: sqlite3.Connection) -> MappingAuditSummary:
    """Classify QCEW industry codes against the 2022 NAICS sector reference."""
    row_counts = _source_code_counts(connection, "source_industry_id")
    statuses = {
        code: classify_industry_code(connection, code) for code in sorted(row_counts)
    }
    return _summary_from_statuses(statuses, row_counts)


def classify_industry_code(connection: sqlite3.Connection, industry_code: str) -> str:
    """Classify one QCEW industry code using exact 2022 NAICS sector evidence."""
    exact = connection.execute(
        """
        SELECT 1
        FROM ref_industry
        WHERE naics_code = ?
          AND naics_version = ?
          AND naics_level = 2;
        """,
        (industry_code, NAICS_ANALYTICAL_VERSION),
    ).fetchone()
    if exact:
        return "directly_comparable"
    return "unresolved"


def compute_growth_rate(current: float | None, prior: float | None) -> float | None:
    """Compute simple percent growth as a decimal when the denominator is valid."""
    if current is None or prior is None or prior <= 0:
        return None
    return (current - prior) / prior


def compute_growth_values(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return rows with growth rates using calendar-year continuity."""
    grouped = _rows_by_panel_year(rows)
    output: list[dict[str, Any]] = []
    for row in rows:
        key = (int(row["geography_id"]), int(row["industry_id"]))
        year = int(row["year"])
        prior = grouped[key].get(year - 1)
        updated = dict(row)
        for value_field, growth_field in (
            ("employment", "employment_growth"),
            ("establishments", "establishment_growth"),
            ("payroll", "payroll_growth"),
            ("average_wage", "wage_growth"),
        ):
            updated[growth_field] = None
            if prior and not prior.get("has_suppression"):
                updated[growth_field] = compute_growth_rate(
                    updated.get(value_field), prior.get(value_field)
                )
        output.append(updated)
    return output


def compute_lag_values(
    rows: list[dict[str, Any]], lag_years: tuple[int, ...] = (1, 2, 3)
) -> list[dict[str, Any]]:
    """Return rows with calendar-year growth lags within geography/industry panels."""
    grouped = _rows_by_panel_year(rows)
    output: list[dict[str, Any]] = []
    for row in rows:
        key = (int(row["geography_id"]), int(row["industry_id"]))
        year = int(row["year"])
        updated = dict(row)
        for lag in lag_years:
            prior = grouped[key].get(year - lag)
            updated[f"employment_growth_lag{lag}"] = (
                prior.get("employment_growth")
                if prior and not prior.get("has_suppression")
                else None
            )
            updated[f"establishment_growth_lag{lag}"] = (
                prior.get("establishment_growth")
                if prior and not prior.get("has_suppression")
                else None
            )
        prior = grouped[key].get(year - 1)
        updated["payroll_growth_lag1"] = (
            prior.get("payroll_growth") if prior and not prior.get("has_suppression") else None
        )
        updated["average_pay_growth_lag1"] = (
            prior.get("wage_growth") if prior and not prior.get("has_suppression") else None
        )
        output.append(updated)
    return output


def _insert_staging_rows(connection: sqlite3.Connection, pipeline_run_id: str) -> None:
    geographies = _county_geography_lookup(connection)
    industries = _industries_by_code(connection)
    selected_rows = _selected_raw_rows(connection)
    groups: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    for raw in selected_rows:
        geography = geographies.get(raw["source_geography_id"])
        status, target = classify_sector(
            source_year_naics("QCEW", raw["source_year"]).native_version,
            raw["source_industry_id"],
        )
        industry = industries.get(target)
        if not geography or not industry:
            continue
        groups.setdefault(
            (geography["geography_id"], industry["industry_id"], raw["source_year"]),
            [],
        ).append(raw | {"geography": geography, "industry": industry, "industry_status": status})

    expected_counties = _expected_counties_by_cbsa(connection)
    for (geography_id, industry_id, year), rows in sorted(groups.items()):
        first = rows[0]
        cbsa_code = first["geography"]["cbsa_code"]
        expected = expected_counties.get(cbsa_code, 0)
        observed_counties = sorted({row["source_geography_id"] for row in rows})
        suppressed_count = sum(1 for row in rows if row["is_suppressed"])
        parsed_rows = [_parsed_measures(row) for row in rows]
        missing_measure_count = sum(1 for row in parsed_rows if any(value is None for value in row))
        complete = (
            expected > 0
            and len(observed_counties) == expected
            and suppressed_count == 0
            and missing_measure_count == 0
        )
        employment = establishments = payroll = average_pay = None
        if complete:
            establishments = sum(row["establishments"] for row in parsed_rows)
            employment = sum(row["employment"] for row in parsed_rows)
            payroll = sum(row["payroll"] for row in parsed_rows)
            average_pay = round(payroll / employment) if employment > 0 else None
        connection.execute(
            """
            INSERT INTO stg_qcew (
                raw_qcew_id,
                manifest_id,
                pipeline_run_id,
                geography_id,
                industry_id,
                year,
                source_geography_id,
                source_industry_id,
                source_ownership_code,
                ownership_scope,
                standardized_cbsa_code,
                standardized_cbsa_name,
                standardized_sector_code,
                geography_mapping_status,
                industry_mapping_status,
                employment,
                establishments,
                payroll,
                average_pay,
                total_annual_wages_nominal,
                average_annual_pay_nominal,
                counties_expected,
                counties_observed,
                counties_suppressed,
                source_row_count,
                is_complete_county_coverage,
                is_missing,
                is_suppressed,
                source_raw_qcew_ids,
                notes
            )
            VALUES (
                NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            );
            """,
            (
                first["manifest_id"],
                pipeline_run_id,
                geography_id,
                industry_id,
                year,
                ",".join(observed_counties),
                first["source_industry_id"],
                PRIVATE_OWNERSHIP_CODE,
                OWNERSHIP_SCOPE,
                cbsa_code,
                first["geography"]["cbsa_name"],
                first["industry"]["naics_code"],
                VALID_GEOGRAPHY_STATUS,
                first["industry_status"],
                employment,
                establishments,
                payroll,
                average_pay,
                payroll,
                average_pay,
                expected,
                len(observed_counties),
                suppressed_count,
                len(rows),
                1 if complete else 0,
                0 if complete else 1,
                1 if suppressed_count else 0,
                json.dumps(sorted(row["raw_qcew_id"] for row in rows)),
                (
                    "County-level QCEW rows aggregated to July 2023 CBSA; "
                    "average annual pay recalculated as total annual wages "
                    "divided by annual average employment. Nominal dollars only."
                ),
            ),
        )


def _insert_intermediate_rows(connection: sqlite3.Connection, pipeline_run_id: str) -> None:
    staged = connection.execute(
        """
        SELECT geography_id,
               industry_id,
               year,
               standardized_cbsa_code,
               standardized_cbsa_name,
               standardized_sector_code,
               employment,
               establishments,
               payroll,
               average_pay,
               total_annual_wages_nominal,
               average_annual_pay_nominal,
               counties_expected,
               counties_observed,
               counties_suppressed,
               is_complete_county_coverage,
               geography_mapping_status,
               industry_mapping_status,
               is_suppressed,
               manifest_id
        FROM stg_qcew
        WHERE geography_mapping_status = ?
          AND industry_mapping_status IN ('directly_comparable', 'official_mapping_required')
          AND is_complete_county_coverage = 1
          AND is_missing = 0;
        """,
        (VALID_GEOGRAPHY_STATUS,),
    ).fetchall()
    for row in staged:
        connection.execute(
            """
            INSERT INTO int_industry_growth (
                geography_id,
                industry_id,
                year,
                standardized_cbsa_code,
                standardized_cbsa_name,
                standardized_sector_code,
                employment,
                establishments,
                payroll,
                average_wage,
                total_annual_wages_nominal,
                average_annual_pay_nominal,
                employment_growth,
                establishment_growth,
                payroll_growth,
                wage_growth,
                employment_growth_lag1,
                employment_growth_lag2,
                employment_growth_lag3,
                establishment_growth_lag1,
                establishment_growth_lag2,
                establishment_growth_lag3,
                payroll_growth_lag1,
                average_pay_growth_lag1,
                counties_expected,
                counties_observed,
                counties_suppressed,
                is_complete_county_coverage,
                geography_mapping_status,
                industry_mapping_status,
                is_real_adjusted,
                has_suppression,
                source_manifest_id,
                pipeline_run_id,
                notes
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL,
                NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?
            );
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
                row[10],
                row[11],
                row[12],
                row[13],
                row[14],
                row[15],
                row[16],
                row[17],
                row[18] or 0,
                row[19],
                pipeline_run_id,
                "A4.8 QCEW industry-growth record; nominal dollars and no source integration.",
            ),
        )


def _apply_growth_rates(connection: sqlite3.Connection) -> None:
    rows = _intermediate_rows(connection)
    for row in compute_growth_values(rows):
        connection.execute(
            """
            UPDATE int_industry_growth
            SET employment_growth = ?,
                establishment_growth = ?,
                payroll_growth = ?,
                wage_growth = ?
            WHERE geography_id = ?
              AND industry_id = ?
              AND year = ?;
            """,
            (
                row["employment_growth"],
                row["establishment_growth"],
                row["payroll_growth"],
                row["wage_growth"],
                row["geography_id"],
                row["industry_id"],
                row["year"],
            ),
        )


def _apply_growth_lags(connection: sqlite3.Connection) -> None:
    rows = _intermediate_rows(connection)
    for row in compute_lag_values(rows):
        connection.execute(
            """
            UPDATE int_industry_growth
            SET employment_growth_lag1 = ?,
                employment_growth_lag2 = ?,
                employment_growth_lag3 = ?,
                establishment_growth_lag1 = ?,
                establishment_growth_lag2 = ?,
                establishment_growth_lag3 = ?,
                payroll_growth_lag1 = ?,
                average_pay_growth_lag1 = ?
            WHERE geography_id = ?
              AND industry_id = ?
              AND year = ?;
            """,
            (
                row["employment_growth_lag1"],
                row["employment_growth_lag2"],
                row["employment_growth_lag3"],
                row["establishment_growth_lag1"],
                row["establishment_growth_lag2"],
                row["establishment_growth_lag3"],
                row["payroll_growth_lag1"],
                row["average_pay_growth_lag1"],
                row["geography_id"],
                row["industry_id"],
                row["year"],
            ),
        )


def _record_exclusions(connection: sqlite3.Connection, pipeline_run_id: str) -> int:
    selected_source_ids = _selected_raw_ids(connection)
    count = 0
    for row in _raw_rows(connection):
        reason = None
        detail = None
        if row["source_ownership_code"] != PRIVATE_OWNERSHIP_CODE:
            reason = "excluded_ownership"
            detail = "QCEW row retained in raw but excluded from private-sector panel."
        elif row["raw_qcew_id"] not in selected_source_ids:
            geography_status = classify_geography_code(connection, row["source_geography_id"])
            industry_status = classify_industry_code(connection, row["source_industry_id"])
            if geography_status == "unresolved":
                reason = "unresolved_geography"
                detail = "County area could not be mapped to July 2023 CBSA crosswalk."
            elif industry_status == "unresolved":
                reason = "unresolved_industry"
                detail = "QCEW industry code is not a directly comparable 2022 NAICS sector."
            else:
                measures = _parsed_measures(row)
                if any(value is None for value in measures):
                    reason = "missing_required_measure"
                    detail = "Required QCEW annual measure is missing or nonnumeric."
        if reason:
            insert_rejected_record(
                connection,
                pipeline_run_id=pipeline_run_id,
                table_name="raw_qcew",
                stage="qcew_standardization",
                reason_code=reason,
                source_row_identifier=row["source_row_identifier"],
                reason_detail=detail,
                serialized_record={
                    "source_geography_id": row["source_geography_id"],
                    "source_industry_id": row["source_industry_id"],
                    "source_ownership_code": row["source_ownership_code"],
                    "source_year": row["source_year"],
                },
            )
            count += 1

    for row in connection.execute(
        """
        SELECT standardized_cbsa_code,
               standardized_sector_code,
               year,
               counties_expected,
               counties_observed,
               counties_suppressed,
               is_missing
        FROM stg_qcew
        WHERE is_complete_county_coverage = 0;
        """
    ).fetchall():
        reason = (
            "suppressed_value" if row[5]
            else "missing_required_measure" if row[6]
            else "incomplete_aggregation"
        )
        detail = {
            "suppressed_value": "County QCEW annual measures include source-suppressed values.",
            "missing_required_measure": "At least one county QCEW annual measure is missing or nonnumeric.",
            "incomplete_aggregation": "The observed county set does not cover the complete CBSA.",
        }[reason]
        insert_rejected_record(
            connection,
            pipeline_run_id=pipeline_run_id,
            table_name="stg_qcew",
            stage="qcew_standardization",
            reason_code=reason,
            source_row_identifier=f"cbsa={row[0]}|sector={row[1]}|year={row[2]}",
            reason_detail=detail,
            serialized_record={
                "counties_expected": row[3],
                "counties_observed": row[4],
                "counties_suppressed": row[5],
                "is_missing": row[6],
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
        "raw_qcew_rows": connection.execute("SELECT COUNT(*) FROM raw_qcew;").fetchone()[0],
        "stg_qcew_rows": connection.execute("SELECT COUNT(*) FROM stg_qcew;").fetchone()[0],
        "int_industry_growth_rows": connection.execute(
            "SELECT COUNT(*) FROM int_industry_growth;"
        ).fetchone()[0],
        "unresolved_geography_rows": geography_audit.row_counts.get("unresolved", 0),
        "unresolved_industry_rows": industry_audit.row_counts.get("unresolved", 0),
        "excluded_ownership_rows": connection.execute(
            "SELECT COUNT(*) FROM raw_qcew WHERE source_ownership_code <> ?;",
            (PRIVATE_OWNERSHIP_CODE,),
        ).fetchone()[0],
        "suppressed_stg_qcew_rows": connection.execute(
            "SELECT COUNT(*) FROM stg_qcew WHERE is_suppressed = 1;"
        ).fetchone()[0],
        "incomplete_aggregation_rows": connection.execute(
            "SELECT COUNT(*) FROM stg_qcew WHERE is_complete_county_coverage = 0;"
        ).fetchone()[0],
        "missing_growth_rows": connection.execute(
            "SELECT COUNT(*) FROM int_industry_growth WHERE employment_growth IS NULL;"
        ).fetchone()[0],
        "duplicate_staging_keys": _duplicate_staging_keys(connection),
        "duplicate_intermediate_keys": _duplicate_intermediate_keys(connection),
        "lag1_missing_rows": connection.execute(
            "SELECT COUNT(*) FROM int_industry_growth WHERE employment_growth_lag1 IS NULL;"
        ).fetchone()[0],
        "valid_msa_sector_panels": connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT geography_id, industry_id
                FROM int_industry_growth
                GROUP BY geography_id, industry_id
            );
            """
        ).fetchone()[0],
        "year_coverage": connection.execute(
            "SELECT COUNT(DISTINCT year) FROM int_industry_growth;"
        ).fetchone()[0],
    }
    for name, value in metrics.items():
        insert_quality_metric(
            connection,
            pipeline_run_id=pipeline_run_id,
            table_name="qcew_a48",
            metric_name=name,
            metric_value=float(value),
            scope="A4.8 QCEW standardization and growth",
        )


def _transform_result(
    connection: sqlite3.Connection,
    pipeline_run_id: str,
    geography_audit: MappingAuditSummary,
    industry_audit: MappingAuditSummary,
) -> QCEWTransformResult:
    return QCEWTransformResult(
        pipeline_run_id=pipeline_run_id,
        staged_rows=connection.execute("SELECT COUNT(*) FROM stg_qcew;").fetchone()[0],
        intermediate_rows=connection.execute(
            "SELECT COUNT(*) FROM int_industry_growth;"
        ).fetchone()[0],
        rejected_rows=connection.execute(
            "SELECT COUNT(*) FROM quality_rejected_record WHERE pipeline_run_id = ?;",
            (pipeline_run_id,),
        ).fetchone()[0],
        duplicate_staging_keys=_duplicate_staging_keys(connection),
        duplicate_intermediate_keys=_duplicate_intermediate_keys(connection),
        suppressed_staging_rows=connection.execute(
            "SELECT COUNT(*) FROM stg_qcew WHERE is_suppressed = 1;"
        ).fetchone()[0],
        incomplete_aggregation_rows=connection.execute(
            "SELECT COUNT(*) FROM stg_qcew WHERE is_complete_county_coverage = 0;"
        ).fetchone()[0],
        missing_growth_rows=connection.execute(
            "SELECT COUNT(*) FROM int_industry_growth WHERE employment_growth IS NULL;"
        ).fetchone()[0],
        employment_growth_lag1_available=connection.execute(
            "SELECT COUNT(*) FROM int_industry_growth WHERE employment_growth_lag1 IS NOT NULL;"
        ).fetchone()[0],
        employment_growth_lag2_available=connection.execute(
            "SELECT COUNT(*) FROM int_industry_growth WHERE employment_growth_lag2 IS NOT NULL;"
        ).fetchone()[0],
        employment_growth_lag3_available=connection.execute(
            "SELECT COUNT(*) FROM int_industry_growth WHERE employment_growth_lag3 IS NOT NULL;"
        ).fetchone()[0],
        establishment_growth_lag1_available=connection.execute(
            "SELECT COUNT(*) FROM int_industry_growth WHERE establishment_growth_lag1 IS NOT NULL;"
        ).fetchone()[0],
        establishment_growth_lag2_available=connection.execute(
            "SELECT COUNT(*) FROM int_industry_growth WHERE establishment_growth_lag2 IS NOT NULL;"
        ).fetchone()[0],
        establishment_growth_lag3_available=connection.execute(
            "SELECT COUNT(*) FROM int_industry_growth WHERE establishment_growth_lag3 IS NOT NULL;"
        ).fetchone()[0],
        geography_audit=geography_audit,
        industry_audit=industry_audit,
    )


def _raw_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT raw_qcew_id,
               manifest_id,
               source_year,
               source_geography_id,
               source_industry_id,
               source_ownership_code,
               source_size_code,
               source_row_identifier,
               annual_avg_estabs,
               annual_avg_emplvl,
               total_annual_wages,
               avg_annual_pay,
               is_suppressed,
               raw_source_filename,
               raw_payload
        FROM raw_qcew
        WHERE source_year BETWEEN 2010 AND 2023;
        """
    ).fetchall()
    return [
        {
            "raw_qcew_id": row[0],
            "manifest_id": row[1],
            "source_year": row[2],
            "source_geography_id": row[3],
            "source_industry_id": row[4],
            "source_ownership_code": row[5],
            "source_size_code": row[6],
            "source_row_identifier": row[7],
            "annual_avg_estabs": row[8],
            "annual_avg_emplvl": row[9],
            "total_annual_wages": row[10],
            "avg_annual_pay": row[11],
            "is_suppressed": bool(row[12]),
            "raw_source_filename": row[13],
            "raw_payload": row[14],
        }
        for row in rows
    ]


def _selected_raw_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    selected = []
    geographies = _county_geography_lookup(connection)
    industries = _industries_by_code(connection)
    for row in _raw_rows(connection):
        if row["source_ownership_code"] != PRIVATE_OWNERSHIP_CODE:
            continue
        if row["source_size_code"] != "0":
            continue
        payload = json.loads(row["raw_payload"])
        if payload.get("qtr") != "A":
            continue
        if row["source_geography_id"] not in geographies:
            continue
        status, target = classify_sector(
            source_year_naics("QCEW", row["source_year"]).native_version,
            row["source_industry_id"],
        )
        if status == "unresolved" or target not in industries:
            continue
        selected.append(row)
    return selected


def _selected_raw_ids(connection: sqlite3.Connection) -> set[int]:
    return {int(row["raw_qcew_id"]) for row in _selected_raw_rows(connection)}


def _parsed_measures(row: dict[str, Any]) -> dict[str, float | None]:
    return {
        "establishments": _to_float(row.get("annual_avg_estabs")),
        "employment": _to_float(row.get("annual_avg_emplvl")),
        "payroll": _to_float(row.get("total_annual_wages")),
        "source_average_pay": _to_float(row.get("avg_annual_pay")),
    }


def _county_geography_lookup(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    return {
        row[0]: {
            "geography_id": row[1],
            "cbsa_code": row[2],
            "cbsa_name": row[3],
        }
        for row in connection.execute(
            """
            SELECT x.county_geoid,
                   x.geography_id,
                   x.cbsa_code,
                   g.cbsa_name
            FROM ref_geography_county_crosswalk AS x
            JOIN ref_geography AS g
              ON g.geography_id = x.geography_id
            WHERE x.source_vintage = ?;
            """,
            (GEOGRAPHY_VINTAGE,),
        )
    }


def _county_crosswalk_record(
    connection: sqlite3.Connection, county_geoid: str
) -> tuple[Any, ...] | None:
    return connection.execute(
        """
        SELECT county_crosswalk_id
        FROM ref_geography_county_crosswalk
        WHERE county_geoid = ?
          AND source_vintage = ?;
        """,
        (county_geoid, GEOGRAPHY_VINTAGE),
    ).fetchone()


def _industries_by_code(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    return {
        row[0]: {"industry_id": row[1], "naics_code": row[0]}
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


def _expected_counties_by_cbsa(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        row[0]: int(row[1])
        for row in connection.execute(
            """
            SELECT cbsa_code, COUNT(*)
            FROM ref_geography_county_crosswalk
            WHERE source_vintage = ?
            GROUP BY cbsa_code;
            """,
            (GEOGRAPHY_VINTAGE,),
        )
    }


def _source_code_counts(connection: sqlite3.Connection, column: str) -> dict[str, int]:
    rows = connection.execute(
        f"""
        SELECT {column}, COUNT(*)
        FROM raw_qcew
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


def _intermediate_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        {
            "geography_id": row[0],
            "industry_id": row[1],
            "year": row[2],
            "employment": row[3],
            "establishments": row[4],
            "payroll": row[5],
            "average_wage": row[6],
            "employment_growth": row[7],
            "establishment_growth": row[8],
            "payroll_growth": row[9],
            "wage_growth": row[10],
            "has_suppression": bool(row[11]),
        }
        for row in connection.execute(
            """
            SELECT geography_id,
                   industry_id,
                   year,
                   employment,
                   establishments,
                   payroll,
                   average_wage,
                   employment_growth,
                   establishment_growth,
                   payroll_growth,
                   wage_growth,
                   has_suppression
            FROM int_industry_growth
            ORDER BY geography_id, industry_id, year;
            """
        )
    ]


def _rows_by_panel_year(
    rows: list[dict[str, Any]]
) -> dict[tuple[int, int], dict[int, dict[str, Any]]]:
    grouped: dict[tuple[int, int], dict[int, dict[str, Any]]] = {}
    for row in rows:
        key = (int(row["geography_id"]), int(row["industry_id"]))
        grouped.setdefault(key, {})[int(row["year"])] = row
    return grouped


def _duplicate_staging_keys(connection: sqlite3.Connection) -> int:
    return connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT geography_id, industry_id, year, source_ownership_code, COUNT(*) AS c
            FROM stg_qcew
            GROUP BY geography_id, industry_id, year, source_ownership_code
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
            FROM int_industry_growth
            GROUP BY geography_id, industry_id, year
            HAVING c > 1
        );
        """
    ).fetchone()[0]


def main() -> None:
    """CLI entry point for the A4.8 QCEW transformation."""
    parser = argparse.ArgumentParser(
        description="Build QCEW staging and industry-growth layers."
    )
    parser.add_argument(
        "--database-path",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the SQLite database file.",
    )
    args = parser.parse_args()
    with connect_database(args.database_path) as connection:
        result = build_qcew_standardized_layers(connection)
    print(
        "Built QCEW standardized layers: "
        f"stg_qcew={result.staged_rows}, "
        f"int_industry_growth={result.intermediate_rows}, "
        f"employment_lag1={result.employment_growth_lag1_available}, "
        f"employment_lag2={result.employment_growth_lag2_available}, "
        f"employment_lag3={result.employment_growth_lag3_available}, "
        f"rejected={result.rejected_rows}"
    )


if __name__ == "__main__":
    main()
