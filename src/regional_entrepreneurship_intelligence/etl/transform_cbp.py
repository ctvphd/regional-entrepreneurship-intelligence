"""CBP standardization and business-structure construction for A4.10."""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

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
from regional_entrepreneurship_intelligence.database.naics_versions import classify_sector
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_cbp import (
    CBP_SAMPLE_PATH,
    load_cbp_raw,
)


VALID_GEOGRAPHY_STATUS = "crosswalk_required"
VALID_INDUSTRY_STATUS = {"directly_comparable", "official_mapping_required"}


@dataclass(frozen=True)
class MappingAuditSummary:
    """Coverage summary for geography or industry mapping."""

    unique_codes: int
    status_counts: dict[str, int]
    row_counts: dict[str, int]


@dataclass(frozen=True)
class CBPTransformResult:
    """Summary returned by the CBP A4.10 build."""

    pipeline_run_id: str
    staged_rows: int
    intermediate_rows: int
    rejected_rows: int
    duplicate_staging_keys: int
    duplicate_intermediate_keys: int
    flagged_staging_rows: int
    incomplete_aggregation_rows: int
    geography_audit: MappingAuditSummary
    industry_audit: MappingAuditSummary


def build_cbp_business_structure(
    connection: sqlite3.Connection,
    *,
    load_raw_if_missing: bool = True,
) -> CBPTransformResult:
    """Build ``stg_cbp`` and ``int_business_structure`` from raw CBP rows."""
    create_schema(connection)
    load_authoritative_reference_data(connection)
    if load_raw_if_missing and connection.execute(
        "SELECT COUNT(*) FROM raw_cbp;"
    ).fetchone()[0] == 0:
        load_cbp_raw(connection, CBP_SAMPLE_PATH)

    run_id = start_pipeline_run(connection, stage="cbp_business_structure")
    try:
        geography_audit = audit_cbp_geography(connection)
        industry_audit = audit_cbp_industry(connection)
        with connection:
            connection.execute("DELETE FROM stg_cbp;")
            connection.execute("DELETE FROM int_business_structure;")
            _insert_staging_rows(connection, run_id)
            _insert_intermediate_rows(connection, run_id)
            rejected_rows = _record_exclusions(connection, run_id)
            _record_quality_metrics(connection, run_id, geography_audit, industry_audit)

        result = _transform_result(connection, run_id, geography_audit, industry_audit)
        finish_pipeline_run(
            connection,
            run_id,
            records_read=connection.execute("SELECT COUNT(*) FROM raw_cbp;").fetchone()[0],
            records_written=result.intermediate_rows,
            records_rejected=rejected_rows,
        )
        return result
    except Exception as exc:
        finish_pipeline_run(connection, run_id, status="failed", error_message=str(exc))
        raise


def audit_cbp_geography(connection: sqlite3.Connection) -> MappingAuditSummary:
    """Classify CBP county GEOIDs against the July 2023 CBSA framework."""
    row_counts = _source_code_counts(connection, "source_county_geoid")
    statuses = {
        code: classify_geography_code(connection, code) for code in sorted(row_counts)
    }
    return _summary_from_statuses(statuses, row_counts)


def classify_geography_code(connection: sqlite3.Connection, county_geoid: str) -> str:
    """Classify one CBP county code for the county-to-CBSA strategy."""
    if _county_crosswalk_record(connection, county_geoid):
        return "crosswalk_required"
    direct = connection.execute(
        """
        SELECT 1
        FROM ref_geography
        WHERE cbsa_code = ?
          AND source_vintage = ?;
        """,
        (county_geoid, GEOGRAPHY_VINTAGE),
    ).fetchone()
    if direct:
        return "direct_match"
    return "unresolved"


def audit_cbp_industry(connection: sqlite3.Connection) -> MappingAuditSummary:
    """Classify CBP 2017 NAICS sector codes against the 2022 sector reference."""
    row_counts = _source_code_counts(connection, "source_industry_id")
    statuses = {
        code: classify_industry_code(connection, code) for code in sorted(row_counts)
    }
    return _summary_from_statuses(statuses, row_counts)


def classify_industry_code(
    connection: sqlite3.Connection, industry_code: str, native_version: str = "2017"
) -> str:
    """Classify a source-native sector using official vintage concordances."""
    status, target = classify_sector(native_version, industry_code)
    if target is None:
        return "unresolved"
    exact = connection.execute(
        """
        SELECT 1
        FROM ref_industry
        WHERE naics_code = ?
          AND naics_version = ?
          AND naics_level = 2;
        """,
        (target, NAICS_ANALYTICAL_VERSION),
    ).fetchone()
    if exact:
        return status
    return "unresolved"


def _insert_staging_rows(connection: sqlite3.Connection, pipeline_run_id: str) -> None:
    geographies = _county_geography_lookup(connection)
    industries = _industries_by_code(connection)
    for raw in _raw_rows(connection):
        geography = geographies.get(raw["source_county_geoid"])
        industry_status, target_sector = classify_sector(
            raw["source_naics_version"], raw["source_industry_id"]
        )
        industry = industries.get(target_sector)
        measures = _parsed_measures(raw)
        connection.execute(
            """
            INSERT INTO stg_cbp (
                raw_cbp_id,
                manifest_id,
                pipeline_run_id,
                geography_id,
                industry_id,
                year,
                source_state_fips,
                source_county_fips,
                source_county_geoid,
                source_county_name,
                source_industry_id,
                source_industry_label,
                source_naics_version,
                standardized_cbsa_code,
                standardized_cbsa_name,
                standardized_sector_code,
                geography_mapping_status,
                industry_mapping_status,
                establishments,
                employment,
                annual_payroll,
                first_quarter_payroll,
                is_missing,
                is_suppressed,
                noise_or_suppression_flags,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                raw["raw_cbp_id"],
                raw["manifest_id"],
                pipeline_run_id,
                geography["geography_id"] if geography else None,
                industry["industry_id"] if industry else None,
                raw["source_year"],
                raw["source_state_fips"],
                raw["source_county_fips"],
                raw["source_county_geoid"],
                raw["source_county_name"],
                raw["source_industry_id"],
                raw["source_industry_label"],
                raw["source_naics_version"],
                geography["cbsa_code"] if geography else None,
                geography["cbsa_name"] if geography else None,
                industry["naics_code"] if industry else None,
                "crosswalk_required" if geography else classify_geography_code(
                    connection, raw["source_county_geoid"]
                ),
                industry_status if industry else "unresolved",
                measures["establishments"],
                measures["employment"],
                measures["annual_payroll"],
                measures["first_quarter_payroll"],
                1 if any(value is None for value in measures.values()) else 0,
                1 if raw["is_suppressed"] else 0,
                _flag_summary(raw),
                "A4.10 CBP county-level staging row; no zero-filling applied.",
            ),
        )


def _insert_intermediate_rows(connection: sqlite3.Connection, pipeline_run_id: str) -> None:
    expected_counties = _expected_counties_by_cbsa(connection)
    groups: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    for row in _eligible_staging_rows(connection):
        groups.setdefault((row["geography_id"], row["industry_id"], row["year"]), []).append(row)

    for (geography_id, industry_id, year), rows in sorted(groups.items()):
        first = rows[0]
        expected = expected_counties.get(first["standardized_cbsa_code"], 0)
        observed_counties = {row["source_county_geoid"] for row in rows}
        suppressed_count = sum(1 for row in rows if row["is_suppressed"])
        complete = expected > 0 and len(observed_counties) == expected and suppressed_count == 0
        if not complete:
            continue
        connection.execute(
            """
            INSERT INTO int_business_structure (
                geography_id,
                industry_id,
                year,
                standardized_cbsa_code,
                standardized_cbsa_name,
                standardized_sector_code,
                establishments,
                employment,
                annual_payroll,
                first_quarter_payroll,
                counties_expected,
                counties_observed,
                counties_suppressed,
                is_complete_county_coverage,
                geography_mapping_status,
                industry_mapping_status,
                has_suppression,
                source_manifest_id,
                pipeline_run_id,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?);
            """,
            (
                geography_id,
                industry_id,
                year,
                first["standardized_cbsa_code"],
                first["standardized_cbsa_name"],
                first["standardized_sector_code"],
                sum(row["establishments"] for row in rows),
                sum(row["employment"] for row in rows),
                sum(row["annual_payroll"] for row in rows),
                sum(row["first_quarter_payroll"] for row in rows),
                expected,
                len(observed_counties),
                suppressed_count,
                first["geography_mapping_status"],
                first["industry_mapping_status"],
                1 if suppressed_count else 0,
                first["manifest_id"],
                pipeline_run_id,
                "A4.10 CBP business-structure record; payroll values remain nominal $1,000.",
            ),
        )


def _record_exclusions(connection: sqlite3.Connection, pipeline_run_id: str) -> int:
    count = 0
    for row in _staging_rows(connection):
        reason = None
        detail = None
        if row["geography_mapping_status"] == "unresolved":
            reason = "unresolved_geography"
            detail = "CBP county could not be mapped to the July 2023 CBSA crosswalk."
        elif row["industry_mapping_status"] == "unresolved":
            reason = "unresolved_industry"
            detail = "CBP industry code is not a directly comparable 2022 NAICS sector."
        elif row["is_suppressed"]:
            reason = "suppressed_value"
            detail = "CBP row contains one or more source flags and is not aggregated."
        elif row["is_missing"]:
            reason = "missing_required_measure"
            detail = "Required CBP business-structure measure is missing or nonnumeric."
        if reason:
            insert_rejected_record(
                connection,
                pipeline_run_id=pipeline_run_id,
                table_name="stg_cbp",
                stage="cbp_business_structure",
                reason_code=reason,
                source_row_identifier=_staging_identifier(row),
                reason_detail=detail,
                serialized_record={
                    "source_county_geoid": row["source_county_geoid"],
                    "source_industry_id": row["source_industry_id"],
                    "year": row["year"],
                },
            )
            count += 1

    for row in _incomplete_groups(connection):
        insert_rejected_record(
            connection,
            pipeline_run_id=pipeline_run_id,
            table_name="stg_cbp",
            stage="cbp_business_structure",
            reason_code="incomplete_aggregation",
            source_row_identifier=f"cbsa={row['cbsa']}|sector={row['sector']}|year={row['year']}",
            reason_detail="CBP group retained in staging but excluded from int_business_structure.",
            serialized_record={
                "counties_expected": row["expected"],
                "counties_observed": row["observed"],
                "counties_suppressed": row["suppressed"],
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
        "raw_cbp_rows": connection.execute("SELECT COUNT(*) FROM raw_cbp;").fetchone()[0],
        "stg_cbp_rows": connection.execute("SELECT COUNT(*) FROM stg_cbp;").fetchone()[0],
        "int_business_structure_rows": connection.execute(
            "SELECT COUNT(*) FROM int_business_structure;"
        ).fetchone()[0],
        "unresolved_geography_rows": geography_audit.row_counts.get("unresolved", 0),
        "unresolved_industry_rows": industry_audit.row_counts.get("unresolved", 0),
        "flagged_stg_cbp_rows": connection.execute(
            "SELECT COUNT(*) FROM stg_cbp WHERE is_suppressed = 1;"
        ).fetchone()[0],
        "incomplete_aggregation_rows": len(_incomplete_groups(connection)),
        "duplicate_staging_keys": _duplicate_staging_keys(connection),
        "duplicate_intermediate_keys": _duplicate_intermediate_keys(connection),
        "msa_count": connection.execute(
            "SELECT COUNT(DISTINCT geography_id) FROM int_business_structure;"
        ).fetchone()[0],
        "sector_count": connection.execute(
            "SELECT COUNT(DISTINCT industry_id) FROM int_business_structure;"
        ).fetchone()[0],
        "year_count": connection.execute(
            "SELECT COUNT(DISTINCT year) FROM int_business_structure;"
        ).fetchone()[0],
    }
    for name, value in metrics.items():
        insert_quality_metric(
            connection,
            pipeline_run_id=pipeline_run_id,
            table_name="cbp_a410",
            metric_name=name,
            metric_value=float(value),
            scope="A4.10 CBP business-structure construction",
        )


def _transform_result(
    connection: sqlite3.Connection,
    pipeline_run_id: str,
    geography_audit: MappingAuditSummary,
    industry_audit: MappingAuditSummary,
) -> CBPTransformResult:
    return CBPTransformResult(
        pipeline_run_id=pipeline_run_id,
        staged_rows=connection.execute("SELECT COUNT(*) FROM stg_cbp;").fetchone()[0],
        intermediate_rows=connection.execute(
            "SELECT COUNT(*) FROM int_business_structure;"
        ).fetchone()[0],
        rejected_rows=connection.execute(
            "SELECT COUNT(*) FROM quality_rejected_record WHERE pipeline_run_id = ?;",
            (pipeline_run_id,),
        ).fetchone()[0],
        duplicate_staging_keys=_duplicate_staging_keys(connection),
        duplicate_intermediate_keys=_duplicate_intermediate_keys(connection),
        flagged_staging_rows=connection.execute(
            "SELECT COUNT(*) FROM stg_cbp WHERE is_suppressed = 1;"
        ).fetchone()[0],
        incomplete_aggregation_rows=_incomplete_aggregation_count(connection),
        geography_audit=geography_audit,
        industry_audit=industry_audit,
    )


def _raw_rows(connection: sqlite3.Connection) -> Iterator[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT raw_cbp_id,
               manifest_id,
               source_year,
               source_geography_id,
               source_state_fips,
               source_county_fips,
               source_county_geoid,
               source_industry_id,
               source_industry_label,
               source_naics_version,
               source_row_identifier,
               establishments,
               employment,
               annual_payroll,
               first_quarter_payroll,
               establishments_flag,
               employment_flag,
               annual_payroll_flag,
               first_quarter_payroll_flag,
               is_suppressed,
               raw_payload
        FROM raw_cbp
        WHERE source_year BETWEEN 2010 AND 2023;
        """
    )
    for row in rows:
        payload = json.loads(row[20])
        yield {
                "raw_cbp_id": row[0],
                "manifest_id": row[1],
                "source_year": row[2],
                "source_geography_id": row[3],
                "source_state_fips": row[4],
                "source_county_fips": row[5],
                "source_county_geoid": row[6],
                "source_county_name": payload.get("county_name"),
                "source_industry_id": row[7],
                "source_industry_label": row[8],
                "source_naics_version": row[9],
                "source_row_identifier": row[10],
                "establishments": row[11],
                "employment": row[12],
                "annual_payroll": row[13],
                "first_quarter_payroll": row[14],
                "establishments_flag": row[15],
                "employment_flag": row[16],
                "annual_payroll_flag": row[17],
                "first_quarter_payroll_flag": row[18],
                "is_suppressed": bool(row[19]),
                "raw_payload": row[20],
            }


def _eligible_staging_rows(connection: sqlite3.Connection) -> Iterator[dict[str, Any]]:
    return (
        row
        for row in _staging_rows(connection)
        if row["geography_mapping_status"] == VALID_GEOGRAPHY_STATUS
        and row["industry_mapping_status"] in VALID_INDUSTRY_STATUS
        and not row["is_missing"]
        and not row["is_suppressed"]
    )


def _staging_rows(connection: sqlite3.Connection) -> Iterator[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT stg_cbp_id,
               geography_id,
               industry_id,
               year,
               source_county_geoid,
               source_industry_id,
               standardized_cbsa_code,
               standardized_cbsa_name,
               standardized_sector_code,
               geography_mapping_status,
               industry_mapping_status,
               establishments,
               employment,
               annual_payroll,
               first_quarter_payroll,
               is_missing,
               is_suppressed,
               manifest_id
        FROM stg_cbp;
        """
    )
    for row in rows:
        yield {
            "stg_cbp_id": row[0],
            "geography_id": row[1],
            "industry_id": row[2],
            "year": row[3],
            "source_county_geoid": row[4],
            "source_industry_id": row[5],
            "standardized_cbsa_code": row[6],
            "standardized_cbsa_name": row[7],
            "standardized_sector_code": row[8],
            "geography_mapping_status": row[9],
            "industry_mapping_status": row[10],
            "establishments": row[11],
            "employment": row[12],
            "annual_payroll": row[13],
            "first_quarter_payroll": row[14],
            "is_missing": bool(row[15]),
            "is_suppressed": bool(row[16]),
            "manifest_id": row[17],
        }


def _parsed_measures(row: dict[str, Any]) -> dict[str, float | None]:
    return {
        "establishments": _to_float(row.get("establishments")),
        "employment": _to_float(row.get("employment")),
        "annual_payroll": _to_float(row.get("annual_payroll")),
        "first_quarter_payroll": _to_float(row.get("first_quarter_payroll")),
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
        FROM raw_cbp
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


def _incomplete_groups(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    expected_counties = _expected_counties_by_cbsa(connection)
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
    for row in _eligible_staging_rows(connection):
        key = (
            row["standardized_cbsa_code"],
            row["standardized_sector_code"],
            int(row["year"]),
        )
        grouped.setdefault(key, []).append(row)

    incomplete = []
    for (cbsa, sector, year), rows in sorted(grouped.items()):
        expected = expected_counties.get(cbsa, 0)
        observed = len({row["source_county_geoid"] for row in rows})
        suppressed = sum(1 for row in rows if row["is_suppressed"])
        if expected == 0 or observed != expected or suppressed:
            incomplete.append(
                {
                    "cbsa": cbsa,
                    "sector": sector,
                    "year": year,
                    "expected": expected,
                    "observed": observed,
                    "suppressed": suppressed,
                }
            )
    return incomplete


def _incomplete_aggregation_count(connection: sqlite3.Connection) -> int:
    return connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT s.standardized_cbsa_code,
                   s.standardized_sector_code,
                   s.year
            FROM stg_cbp AS s
            WHERE s.geography_mapping_status = ?
              AND s.industry_mapping_status IN ('directly_comparable', 'official_mapping_required')
              AND s.is_missing = 0
              AND s.is_suppressed = 0
            GROUP BY s.standardized_cbsa_code, s.standardized_sector_code, s.year
            HAVING COUNT(DISTINCT s.source_county_geoid) < COALESCE((
                SELECT COUNT(*)
                FROM ref_geography_county_crosswalk AS x
                WHERE x.cbsa_code = s.standardized_cbsa_code
                  AND x.source_vintage = ?
            ), 0)
        );
        """,
        (VALID_GEOGRAPHY_STATUS, GEOGRAPHY_VINTAGE),
    ).fetchone()[0]


def _flag_summary(row: dict[str, Any]) -> str | None:
    flags = {
        key: row.get(key)
        for key in (
            "establishments_flag",
            "employment_flag",
            "annual_payroll_flag",
            "first_quarter_payroll_flag",
        )
        if (row.get(key) or "").strip()
    }
    return json.dumps(flags, sort_keys=True) if flags else None


def _staging_identifier(row: dict[str, Any]) -> str:
    return (
        f"cbp_county|year={row['year']}|county={row['source_county_geoid']}"
        f"|industry={row['source_industry_id']}"
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


def _duplicate_staging_keys(connection: sqlite3.Connection) -> int:
    return connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT source_county_geoid, source_industry_id, year, COUNT(*) AS c
            FROM stg_cbp
            GROUP BY source_county_geoid, source_industry_id, year
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
            FROM int_business_structure
            GROUP BY geography_id, industry_id, year
            HAVING c > 1
        );
        """
    ).fetchone()[0]


def main() -> None:
    """CLI entry point for the A4.10 CBP transformation."""
    parser = argparse.ArgumentParser(
        description="Build CBP staging and business-structure layers."
    )
    parser.add_argument(
        "--database-path",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the SQLite database file.",
    )
    args = parser.parse_args()
    with connect_database(args.database_path) as connection:
        result = build_cbp_business_structure(connection)
    print(
        "Built CBP business-structure layers: "
        f"stg_cbp={result.staged_rows}, "
        f"int_business_structure={result.intermediate_rows}, "
        f"flagged={result.flagged_staging_rows}, "
        f"incomplete={result.incomplete_aggregation_rows}, "
        f"rejected={result.rejected_rows}"
    )


if __name__ == "__main__":
    main()
