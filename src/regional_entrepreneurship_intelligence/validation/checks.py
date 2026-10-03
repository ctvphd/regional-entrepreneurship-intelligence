"""Small reusable checks for production and test database validation."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable


def validate_required_columns(
    connection: sqlite3.Connection, table: str, columns: Iterable[str]
) -> None:
    """Raise when a table does not contain every required column."""
    actual = {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}
    missing = set(columns) - actual
    if missing:
        raise ValueError(f"{table} is missing required columns: {sorted(missing)}")


def validate_unique_key(
    connection: sqlite3.Connection, table: str, columns: Iterable[str]
) -> int:
    """Validate a composite key and return its duplicate-group count."""
    names = tuple(columns)
    if not names:
        raise ValueError("A unique-key check requires at least one column")
    validate_required_columns(connection, table, names)
    quoted = ", ".join(f'"{name}"' for name in names)
    duplicates = connection.execute(
        f"SELECT COUNT(*) FROM (SELECT {quoted} FROM \"{table}\" "
        f"GROUP BY {quoted} HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    if duplicates:
        raise ValueError(f"{table} has {duplicates} duplicate groups at key {names}")
    return duplicates


def validate_year_range(
    connection: sqlite3.Connection, table: str, column: str, minimum: int, maximum: int
) -> None:
    """Require all non-null years to lie within the inclusive range."""
    validate_required_columns(connection, table, (column,))
    invalid = connection.execute(
        f'SELECT COUNT(*) FROM "{table}" WHERE "{column}" IS NULL '
        f'OR "{column}" < ? OR "{column}" > ?', (minimum, maximum)
    ).fetchone()[0]
    if invalid:
        raise ValueError(f"{table}.{column} has {invalid} rows outside {minimum}-{maximum}")


def validate_nonnegative(
    connection: sqlite3.Connection, table: str, columns: Iterable[str]
) -> None:
    """Require every non-null value in each named column to be nonnegative."""
    names = tuple(columns)
    validate_required_columns(connection, table, names)
    for name in names:
        invalid = connection.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE "{name}" < 0'
        ).fetchone()[0]
        if invalid:
            raise ValueError(f"{table}.{name} has {invalid} negative values")


def validate_percentage_bounds(
    connection: sqlite3.Connection, table: str, columns: Iterable[str]
) -> None:
    """Require non-null percentage values to lie between zero and 100."""
    names = tuple(columns)
    validate_required_columns(connection, table, names)
    for name in names:
        invalid = connection.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE "{name}" < 0 OR "{name}" > 100'
        ).fetchone()[0]
        if invalid:
            raise ValueError(f"{table}.{name} has {invalid} values outside [0, 100]")


def validate_no_leakage_columns(
    connection: sqlite3.Connection, table: str, prohibited: Iterable[str]
) -> None:
    """Require that prohibited downstream target columns are absent."""
    present = {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}
    overlap = present & set(prohibited)
    if overlap:
        raise ValueError(f"{table} contains prohibited leakage columns: {sorted(overlap)}")
