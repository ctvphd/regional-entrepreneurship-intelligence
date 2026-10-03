"""Metadata and quality helper functions for Assignment 4.3."""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any


PIPELINE_STATUSES = {"planned", "running", "success", "failed", "partial"}

REJECTION_REASON_CODES = {
    "invalid_cbsa",
    "invalid_naics",
    "invalid_year",
    "duplicate_key",
    "missing_required_field",
    "invalid_numeric_value",
    "suppressed_value",
    "failed_reference_match",
    "unresolved_geography",
    "unresolved_industry",
    "excluded_ownership",
    "duplicate_standardized_key",
    "incomplete_aggregation",
    "missing_required_measure",
    "missing_required_startup_measure",
    "other",
}


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp without microseconds."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _require_text(value: str | None, field_name: str) -> str:
    if value is None or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value


def _validate_nonnegative(value: int | None, field_name: str) -> int | None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _serialize_record(record: Mapping[str, Any] | str | None) -> str | None:
    if record is None or isinstance(record, str):
        return record
    return json.dumps(record, sort_keys=True)


def insert_source_manifest(
    connection: sqlite3.Connection,
    *,
    source_name: str,
    dataset_name: str,
    access_method: str,
    source_year: int,
    raw_filename: str,
    file_checksum: str,
    row_count: int,
    source_id: int | None = None,
    source_agency: str | None = None,
    source_url_or_endpoint: str | None = None,
    retrieval_timestamp: str | None = None,
    source_version: str | None = None,
    notes: str | None = None,
) -> int:
    """Insert a source manifest row and return its primary key."""
    _require_text(source_name, "source_name")
    _require_text(dataset_name, "dataset_name")
    _require_text(access_method, "access_method")
    _require_text(raw_filename, "raw_filename")
    _require_text(file_checksum, "file_checksum")
    _validate_nonnegative(row_count, "row_count")

    timestamp = retrieval_timestamp or utc_timestamp()
    with connection:
        cursor = connection.execute(
            """
            INSERT INTO metadata_source_manifest (
                source_id,
                source_name,
                source_agency,
                dataset_name,
                access_method,
                source_url_or_endpoint,
                retrieval_timestamp,
                source_year,
                source_version,
                raw_filename,
                file_checksum,
                row_count,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                source_id,
                source_name,
                source_agency,
                dataset_name,
                access_method,
                source_url_or_endpoint,
                timestamp,
                source_year,
                source_version,
                raw_filename,
                file_checksum,
                row_count,
                notes,
            ),
        )
    return int(cursor.lastrowid)


def start_pipeline_run(
    connection: sqlite3.Connection,
    *,
    stage: str,
    pipeline_run_id: str | None = None,
    start_timestamp: str | None = None,
    warnings: str | None = None,
) -> str:
    """Create a running pipeline metadata row and return its run id."""
    run_id = pipeline_run_id or str(uuid.uuid4())
    _require_text(stage, "stage")

    with connection:
        connection.execute(
            """
            INSERT INTO metadata_pipeline_run (
                pipeline_run_id,
                start_timestamp,
                status,
                stage,
                records_read,
                records_written,
                records_rejected,
                warnings
            )
            VALUES (?, ?, 'running', ?, 0, 0, 0, ?);
            """,
            (run_id, start_timestamp or utc_timestamp(), stage, warnings),
        )
    return run_id


def update_pipeline_run(
    connection: sqlite3.Connection,
    pipeline_run_id: str,
    **fields: Any,
) -> None:
    """Update selected fields on a pipeline run."""
    allowed_fields = {
        "end_timestamp",
        "status",
        "stage",
        "records_read",
        "records_written",
        "records_rejected",
        "warnings",
        "error_message",
    }
    unknown_fields = set(fields) - allowed_fields
    if unknown_fields:
        raise ValueError(f"Unsupported pipeline-run fields: {sorted(unknown_fields)}")
    if "status" in fields and fields["status"] not in PIPELINE_STATUSES:
        raise ValueError(f"Unsupported pipeline status: {fields['status']}")
    for count_field in ("records_read", "records_written", "records_rejected"):
        if count_field in fields:
            _validate_nonnegative(fields[count_field], count_field)
    if not fields:
        return

    assignments = ", ".join(f"{field} = ?" for field in fields)
    values = [fields[field] for field in fields]
    values.append(pipeline_run_id)
    with connection:
        cursor = connection.execute(
            f"""
            UPDATE metadata_pipeline_run
            SET {assignments}
            WHERE pipeline_run_id = ?;
            """,
            values,
        )
    if cursor.rowcount == 0:
        raise KeyError(f"Unknown pipeline_run_id: {pipeline_run_id}")


def finish_pipeline_run(
    connection: sqlite3.Connection,
    pipeline_run_id: str,
    *,
    status: str = "success",
    records_read: int | None = None,
    records_written: int | None = None,
    records_rejected: int | None = None,
    warnings: str | None = None,
    error_message: str | None = None,
    end_timestamp: str | None = None,
) -> None:
    """Mark a pipeline run as finished."""
    fields: dict[str, Any] = {
        "status": status,
        "end_timestamp": end_timestamp or utc_timestamp(),
    }
    optional_updates = {
        "records_read": records_read,
        "records_written": records_written,
        "records_rejected": records_rejected,
        "warnings": warnings,
        "error_message": error_message,
    }
    fields.update(
        {field: value for field, value in optional_updates.items() if value is not None}
    )
    update_pipeline_run(connection, pipeline_run_id, **fields)


def insert_quality_metric(
    connection: sqlite3.Connection,
    *,
    table_name: str,
    metric_name: str,
    metric_value: float,
    pipeline_run_id: str | None = None,
    year: int | None = None,
    scope: str | None = None,
    notes: str | None = None,
) -> int:
    """Store a table-level quality metric and return its primary key."""
    _require_text(table_name, "table_name")
    _require_text(metric_name, "metric_name")

    statement = """
        INSERT INTO quality_table_metric (
            pipeline_run_id, table_name, metric_name, metric_value,
            year, scope, notes, created_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """
    parameters = (
        pipeline_run_id, table_name, metric_name, metric_value,
        year, scope, notes, utc_timestamp(),
    )
    cursor = _write_in_current_transaction(connection, statement, parameters)
    return int(cursor.lastrowid)


def insert_rejected_record(
    connection: sqlite3.Connection,
    *,
    table_name: str,
    stage: str,
    reason_code: str,
    pipeline_run_id: str | None = None,
    source_id: int | None = None,
    source_row_identifier: str | None = None,
    reason_detail: str | None = None,
    original_value: str | None = None,
    serialized_record: Mapping[str, Any] | str | None = None,
) -> int:
    """Store a rejected or reviewed synthetic/source record and return its key."""
    _require_text(table_name, "table_name")
    _require_text(stage, "stage")
    if reason_code not in REJECTION_REASON_CODES:
        raise ValueError(f"Unsupported rejection reason_code: {reason_code}")

    statement = """
        INSERT INTO quality_rejected_record (
            pipeline_run_id, source_id, table_name, stage,
            source_row_identifier, reason_code, reason_detail,
            original_value, serialized_record, created_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    parameters = (
        pipeline_run_id, source_id, table_name, stage, source_row_identifier,
        reason_code, reason_detail, original_value,
        _serialize_record(serialized_record), utc_timestamp(),
    )
    cursor = _write_in_current_transaction(connection, statement, parameters)
    return int(cursor.lastrowid)


def _write_in_current_transaction(
    connection: sqlite3.Connection, statement: str, parameters: tuple[Any, ...]
) -> sqlite3.Cursor:
    """Avoid committing each helper call when the caller owns a transaction."""
    if connection.in_transaction:
        return connection.execute(statement, parameters)
    with connection:
        return connection.execute(statement, parameters)
