"""Reference-table seed and loading helpers.

This module loads deterministic project reference rows and small authoritative
reference assets. It does not ingest BDS, QCEW, CBP, or ACS observations.
"""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from regional_entrepreneurship_intelligence.database.connection import (
    DEFAULT_DATABASE_PATH,
    PROJECT_ROOT,
    connect_database,
)
from regional_entrepreneurship_intelligence.database.metadata import (
    insert_source_manifest,
)
from regional_entrepreneurship_intelligence.database.schema import (
    create_schema,
    seed_ref_year,
)


DEFAULT_REFERENCE_DIR = PROJECT_ROOT / "data" / "external" / "reference"
GEOGRAPHY_VINTAGE = "July 2023 CBSA delineation"
NAICS_ANALYTICAL_VERSION = "2022"

OFFICIAL_REFERENCE_ASSETS: tuple[dict[str, str | int | None], ...] = (
    {
        "filename": "list1_2023.xlsx",
        "source_name": "Census CBSA Delineation Files",
        "source_agency": "U.S. Census Bureau",
        "dataset_name": "Core Based Statistical Areas, Metropolitan Divisions, and Combined Statistical Areas",
        "access_method": "official public HTTPS download",
        "url": "https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx",
        "source_year": 2023,
        "source_version": GEOGRAPHY_VINTAGE,
        "notes": "Official July 2023 CBSA delineation List 1; used for fixed-vintage geography and county-to-CBSA membership.",
    },
    {
        "filename": "2022_NAICS_Structure.xlsx",
        "source_name": "North American Industry Classification System (NAICS)",
        "source_agency": "U.S. Census Bureau",
        "dataset_name": "2022 NAICS Structure with Change Indicator",
        "access_method": "official public HTTPS download",
        "url": "https://www.census.gov/naics/2022NAICS/2022_NAICS_Structure.xlsx",
        "source_year": 2022,
        "source_version": "2022 NAICS",
        "notes": "Authoritative 2022 NAICS structure used as the analytical industry reference.",
    },
    {
        "filename": "2022_to_2017_NAICS.xlsx",
        "source_name": "North American Industry Classification System (NAICS)",
        "source_agency": "U.S. Census Bureau",
        "dataset_name": "2022 NAICS to 2017 NAICS concordance",
        "access_method": "official public HTTPS download",
        "url": "https://www.census.gov/naics/concordances/2022_to_2017_NAICS.xlsx",
        "source_year": 2022,
        "source_version": "2022-to-2017 NAICS concordance",
        "notes": "Preserved for later source-specific NAICS version mapping; not applied automatically in A4.4.",
    },
    {
        "filename": "2017_to_2022_NAICS.xlsx",
        "source_name": "North American Industry Classification System (NAICS)",
        "source_agency": "U.S. Census Bureau",
        "dataset_name": "2017 NAICS to 2022 NAICS concordance",
        "access_method": "official public HTTPS download",
        "url": "https://www.census.gov/naics/concordances/2017_to_2022_NAICS.xlsx",
        "source_year": 2017,
        "source_version": "2017-to-2022 NAICS concordance",
        "notes": "Preserved for later source-specific NAICS version mapping; not applied automatically in A4.4.",
    },
    {
        "filename": "2017_to_2012_NAICS.xlsx",
        "source_name": "North American Industry Classification System (NAICS)",
        "source_agency": "U.S. Census Bureau",
        "dataset_name": "2017 NAICS to 2012 NAICS concordance",
        "access_method": "official public HTTPS download",
        "url": "https://www.census.gov/naics/concordances/2017_to_2012_NAICS.xlsx",
        "source_year": 2017,
        "source_version": "2017-to-2012 NAICS concordance",
        "notes": "Preserved for later source-specific NAICS version mapping; not applied automatically in A4.4.",
    },
    {
        "filename": "2012_to_2017_NAICS.xlsx",
        "source_name": "North American Industry Classification System (NAICS)",
        "source_agency": "U.S. Census Bureau",
        "dataset_name": "2012 NAICS to 2017 NAICS concordance",
        "access_method": "official public HTTPS download",
        "url": "https://www.census.gov/naics/concordances/2012_to_2017_NAICS.xlsx",
        "source_year": 2012,
        "source_version": "2012-to-2017 NAICS concordance",
        "notes": "Preserved for later source-specific NAICS version mapping; not applied automatically in A4.4.",
    },
)


APPROVED_SOURCES: tuple[dict[str, str | None], ...] = (
    {
        "source_name": "Census Business Dynamics Statistics (BDS)",
        "source_agency": "U.S. Census Bureau",
        "dataset_name": "Business Dynamics Statistics",
        "default_access_method": "API or bulk file",
        "homepage_url": None,
        "notes": "Source URL or endpoint will be verified during BDS-specific ingestion.",
    },
    {
        "source_name": "BLS Quarterly Census of Employment and Wages (QCEW)",
        "source_agency": "U.S. Bureau of Labor Statistics",
        "dataset_name": "Quarterly Census of Employment and Wages",
        "default_access_method": "official bulk files",
        "homepage_url": None,
        "notes": "Bulk-file location will be verified during QCEW-specific ingestion.",
    },
    {
        "source_name": "Census County Business Patterns (CBP)",
        "source_agency": "U.S. Census Bureau",
        "dataset_name": "County Business Patterns",
        "default_access_method": "API initially; bulk files if needed",
        "homepage_url": None,
        "notes": "Source URL or endpoint will be verified during CBP-specific ingestion.",
    },
    {
        "source_name": "American Community Survey (ACS)",
        "source_agency": "U.S. Census Bureau",
        "dataset_name": "American Community Survey",
        "default_access_method": "API",
        "homepage_url": None,
        "notes": "Source URL or endpoint will be verified during ACS-specific ingestion.",
    },
)


@dataclass(frozen=True)
class ReferenceLoadResult:
    """Summary returned by the authoritative reference loader."""

    ref_geography_count: int
    ref_geography_county_crosswalk_count: int
    ref_industry_count: int
    manifest_ids: tuple[int, ...]


def seed_ref_source(connection: sqlite3.Connection) -> None:
    """Populate the approved source registry without fetching source records."""
    connection.executemany(
        """
        INSERT INTO ref_source (
            source_name,
            source_agency,
            dataset_name,
            default_access_method,
            homepage_url,
            notes
        )
        VALUES (
            :source_name,
            :source_agency,
            :dataset_name,
            :default_access_method,
            :homepage_url,
            :notes
        )
        ON CONFLICT(source_name) DO UPDATE SET
            source_agency = excluded.source_agency,
            dataset_name = excluded.dataset_name,
            default_access_method = excluded.default_access_method,
            homepage_url = excluded.homepage_url,
            notes = excluded.notes;
        """,
        APPROVED_SOURCES,
    )


def seed_reference_data(connection: sqlite3.Connection) -> None:
    """Seed deterministic reference tables that are verified for A4.3.

    Geography and industry references are intentionally not populated here.
    Those tables require authoritative CBSA and NAICS reference/crosswalk files
    that have not yet been added to the repository.
    """
    connection.execute("PRAGMA foreign_keys = ON;")
    with connection:
        seed_ref_year(connection)
        seed_ref_source(connection)


def get_reference_counts(connection: sqlite3.Connection) -> dict[str, int]:
    """Return row counts for all reference tables."""
    tables = (
        "ref_year",
        "ref_source",
        "ref_geography",
        "ref_geography_county_crosswalk",
        "ref_industry",
    )
    return {
        table: int(
            connection.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
        )
        for table in tables
    }


def list_approved_source_names() -> tuple[str, ...]:
    """Return the approved source names in deterministic order."""
    return tuple(str(source["source_name"]) for source in APPROVED_SOURCES)


def approved_source_by_name(source_name: str) -> dict[str, Any]:
    """Return one approved source definition by name."""
    for source in APPROVED_SOURCES:
        if source["source_name"] == source_name:
            return dict(source)
    raise KeyError(f"Unknown approved source: {source_name}")


def load_authoritative_reference_data(
    connection: sqlite3.Connection,
    *,
    reference_dir: str | Path = DEFAULT_REFERENCE_DIR,
) -> ReferenceLoadResult:
    """Load A4.4 authoritative geography and NAICS reference assets."""
    reference_path = Path(reference_dir)
    seed_reference_data(connection)
    manifest_ids = tuple(
        _ensure_reference_asset_manifest(connection, reference_path, asset)
        for asset in OFFICIAL_REFERENCE_ASSETS
    )
    load_geography_reference(connection, reference_path / "list1_2023.xlsx")
    load_industry_reference(connection, reference_path / "2022_NAICS_Structure.xlsx")
    counts = get_reference_counts(connection)
    return ReferenceLoadResult(
        ref_geography_count=counts["ref_geography"],
        ref_geography_county_crosswalk_count=counts[
            "ref_geography_county_crosswalk"
        ],
        ref_industry_count=counts["ref_industry"],
        manifest_ids=manifest_ids,
    )


def load_geography_reference(
    connection: sqlite3.Connection,
    workbook_path: str | Path,
    *,
    source_vintage: str = GEOGRAPHY_VINTAGE,
) -> None:
    """Load CBSA and county-membership records from Census List 1."""
    rows = list(_xlsx_rows(Path(workbook_path)))
    expected_header = [
        "CBSA Code",
        "Metropolitan Division Code",
        "CSA Code",
        "CBSA Title",
        "Metropolitan/Micropolitan Statistical Area",
        "Metropolitan Division Title",
        "CSA Title",
        "County/County Equivalent",
        "State Name",
        "FIPS State Code",
        "FIPS County Code",
        "Central/Outlying County",
    ]
    header = rows[2][: len(expected_header)]
    if header != expected_header:
        raise ValueError(f"Unexpected CBSA delineation header: {header}")

    geographies: dict[str, dict[str, Any]] = {}
    counties: list[dict[str, str]] = []
    states_by_cbsa: dict[str, set[str]] = defaultdict(set)
    for row in rows[3:]:
        raw_cbsa_code = _normalize_text(row[0] if row else "")
        if not raw_cbsa_code:
            continue
        if not raw_cbsa_code.isdigit():
            continue
        cbsa_code = _normalize_code(raw_cbsa_code, 5)
        cbsa_name = _require_value(row, 3, "CBSA Title")
        source_type = _require_value(
            row, 4, "Metropolitan/Micropolitan Statistical Area"
        )
        geography_type = _geography_type(source_type)
        state_fips = _normalize_code(_require_value(row, 9, "FIPS State Code"), 2)
        county_fips = _normalize_code(_require_value(row, 10, "FIPS County Code"), 3)
        county_geoid = f"{state_fips}{county_fips}"
        states_by_cbsa[cbsa_code].add(state_fips)
        geographies[cbsa_code] = {
            "cbsa_code": cbsa_code,
            "cbsa_name": cbsa_name,
            "geography_type": geography_type,
            "source_vintage": source_vintage,
            "notes": "Loaded from Census CBSA delineation List 1, July 2023.",
        }
        counties.append(
            {
                "cbsa_code": cbsa_code,
                "county_name": _require_value(row, 7, "County/County Equivalent"),
                "state_name": _require_value(row, 8, "State Name"),
                "state_fips": state_fips,
                "county_fips": county_fips,
                "county_geoid": county_geoid,
                "central_outlying": _require_value(row, 11, "Central/Outlying County"),
                "source_vintage": source_vintage,
                "notes": "County membership from Census CBSA delineation List 1, July 2023.",
            }
        )

    with connection:
        for geography in sorted(geographies.values(), key=lambda item: item["cbsa_code"]):
            state_codes = ",".join(sorted(states_by_cbsa[geography["cbsa_code"]]))
            connection.execute(
                """
                INSERT INTO ref_geography (
                    cbsa_code,
                    cbsa_name,
                    geography_type,
                    state_codes,
                    valid_from_year,
                    valid_to_year,
                    source_vintage,
                    is_active,
                    notes
                )
                VALUES (?, ?, ?, ?, NULL, NULL, ?, 1, ?)
                ON CONFLICT(cbsa_code, source_vintage) DO UPDATE SET
                    cbsa_name = excluded.cbsa_name,
                    geography_type = excluded.geography_type,
                    state_codes = excluded.state_codes,
                    valid_from_year = excluded.valid_from_year,
                    valid_to_year = excluded.valid_to_year,
                    is_active = excluded.is_active,
                    notes = excluded.notes;
                """,
                (
                    geography["cbsa_code"],
                    geography["cbsa_name"],
                    geography["geography_type"],
                    state_codes,
                    geography["source_vintage"],
                    geography["notes"],
                ),
            )

        geography_ids = {
            row[0]: row[1]
            for row in connection.execute(
                """
                SELECT cbsa_code, geography_id
                FROM ref_geography
                WHERE source_vintage = ?;
                """,
                (source_vintage,),
            )
        }

        for county in counties:
            connection.execute(
                """
                INSERT INTO ref_geography_county_crosswalk (
                    geography_id,
                    cbsa_code,
                    county_name,
                    state_name,
                    state_fips,
                    county_fips,
                    county_geoid,
                    central_outlying,
                    source_vintage,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cbsa_code, county_geoid, source_vintage) DO UPDATE SET
                    geography_id = excluded.geography_id,
                    county_name = excluded.county_name,
                    state_name = excluded.state_name,
                    state_fips = excluded.state_fips,
                    county_fips = excluded.county_fips,
                    central_outlying = excluded.central_outlying,
                    notes = excluded.notes;
                """,
                (
                    geography_ids[county["cbsa_code"]],
                    county["cbsa_code"],
                    county["county_name"],
                    county["state_name"],
                    county["state_fips"],
                    county["county_fips"],
                    county["county_geoid"],
                    county["central_outlying"],
                    county["source_vintage"],
                    county["notes"],
                ),
            )


def load_industry_reference(
    connection: sqlite3.Connection,
    workbook_path: str | Path,
    *,
    naics_version: str = NAICS_ANALYTICAL_VERSION,
) -> None:
    """Load the authoritative Census NAICS structure file."""
    rows = list(_xlsx_rows(Path(workbook_path)))
    expected_header = ["Change Indicator", "2022 NAICS Code", "2022 NAICS Title"]
    header = rows[2][: len(expected_header)]
    if header != expected_header:
        raise ValueError(f"Unexpected NAICS structure header: {header}")

    records: list[dict[str, Any]] = []
    codes: set[str] = set()
    for row in rows[3:]:
        if len(row) < 3 or not _normalize_text(row[1]):
            continue
        code = _normalize_text(row[1])
        title = _normalize_text(row[2])
        if not _is_valid_naics_code(code):
            raise ValueError(f"Unexpected NAICS code format: {code}")
        clean_title, title_note = _clean_naics_title(title)
        codes.add(code)
        records.append(
            {
                "naics_code": code,
                "naics_level": _naics_level(code),
                "naics_title": clean_title,
                "naics_version": naics_version,
                "change_indicator": _normalize_text(row[0]) or None,
                "title_note": title_note,
            }
        )

    with connection:
        for record in records:
            parent_code = _parent_naics_code(record["naics_code"], codes)
            notes = _naics_notes(record["change_indicator"], record["title_note"])
            connection.execute(
                """
                INSERT INTO ref_industry (
                    naics_code,
                    naics_level,
                    naics_title,
                    naics_version,
                    parent_naics_code,
                    is_active,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(naics_code, naics_version) DO UPDATE SET
                    naics_level = excluded.naics_level,
                    naics_title = excluded.naics_title,
                    parent_naics_code = excluded.parent_naics_code,
                    is_active = excluded.is_active,
                    notes = excluded.notes;
                """,
                (
                    record["naics_code"],
                    record["naics_level"],
                    record["naics_title"],
                    record["naics_version"],
                    parent_code,
                    notes,
                ),
            )


def _ensure_reference_asset_manifest(
    connection: sqlite3.Connection,
    reference_dir: Path,
    asset: dict[str, str | int | None],
) -> int:
    file_path = reference_dir / str(asset["filename"])
    if not file_path.exists():
        raise FileNotFoundError(f"Missing official reference asset: {file_path}")
    checksum = _sha256(file_path)
    existing = connection.execute(
        """
        SELECT manifest_id
        FROM metadata_source_manifest
        WHERE raw_filename = ?
          AND file_checksum = ?
          AND source_url_or_endpoint = ?;
        """,
        (asset["filename"], checksum, asset["url"]),
    ).fetchone()
    if existing:
        return int(existing[0])
    return insert_source_manifest(
        connection,
        source_name=str(asset["source_name"]),
        source_agency=str(asset["source_agency"]),
        dataset_name=str(asset["dataset_name"]),
        access_method=str(asset["access_method"]),
        source_url_or_endpoint=str(asset["url"]),
        source_year=int(asset["source_year"]),
        source_version=str(asset["source_version"]),
        raw_filename=str(asset["filename"]),
        file_checksum=checksum,
        row_count=_reference_asset_row_count(file_path),
        notes=str(asset["notes"]),
    )


def _reference_asset_row_count(file_path: Path) -> int:
    rows = list(_xlsx_rows(file_path))
    if file_path.name == "list1_2023.xlsx":
        return sum(
            1
            for row in rows[3:]
            if row and _normalize_text(row[0]).isdigit()
        )
    return sum(1 for row in rows[3:] if any(_normalize_text(value) for value in row))


def _xlsx_rows(path: Path) -> list[list[str]]:
    namespace = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as workbook:
        shared_strings = _shared_strings(workbook, namespace)
        sheet_xml = workbook.read("xl/worksheets/sheet1.xml")
    root = ElementTree.fromstring(sheet_xml)
    rows: list[list[str]] = []
    for row_element in root.findall(".//a:sheetData/a:row", namespace):
        values: dict[int, str] = {}
        for cell in row_element.findall("a:c", namespace):
            index = _column_index(cell.get("r", "A1"))
            values[index] = _cell_value(cell, shared_strings, namespace)
        if values:
            width = max(values) + 1
            rows.append([values.get(index, "") for index in range(width)])
    return rows


def _shared_strings(
    workbook: zipfile.ZipFile, namespace: dict[str, str]
) -> list[str]:
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []
    root = ElementTree.fromstring(workbook.read("xl/sharedStrings.xml"))
    return [
        "".join(text.text or "" for text in item.findall(".//a:t", namespace))
        for item in root.findall("a:si", namespace)
    ]


def _cell_value(
    cell: ElementTree.Element,
    shared_strings: list[str],
    namespace: dict[str, str],
) -> str:
    if cell.get("t") == "inlineStr":
        return "".join(
            text.text or "" for text in cell.findall(".//a:is/a:t", namespace)
        )
    value = cell.find("a:v", namespace)
    if value is None or value.text is None:
        return ""
    raw_value = value.text
    if cell.get("t") == "s":
        return shared_strings[int(raw_value)]
    return raw_value


def _column_index(cell_reference: str) -> int:
    letters = "".join(character for character in cell_reference if character.isalpha())
    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter.upper()) - ord("A") + 1)
    return index - 1


def _normalize_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _normalize_code(value: Any, width: int) -> str:
    return _normalize_text(value).zfill(width)


def _require_value(row: list[str], index: int, field_name: str) -> str:
    value = _normalize_text(row[index] if index < len(row) else "")
    if not value:
        raise ValueError(f"Missing required value for {field_name}")
    return value


def _geography_type(source_type: str) -> str:
    if source_type == "Metropolitan Statistical Area":
        return "MSA"
    if source_type == "Micropolitan Statistical Area":
        return "MICROPOLITAN"
    raise ValueError(f"Unsupported CBSA geography type: {source_type}")


def _clean_naics_title(title: str) -> tuple[str, str | None]:
    if title.endswith("T"):
        return title[:-1].strip(), "Official Census title carried a trilateral-agreement marker."
    return title.strip(), None


def _parent_naics_code(code: str, codes: set[str]) -> str | None:
    if _naics_level(code) == 2:
        return None
    for length in range(len(code) - 1, 1, -1):
        candidate = code[:length]
        if candidate in codes:
            return candidate
    sector_code = code[:2]
    for candidate in codes:
        if _sector_range_contains(candidate, sector_code):
            return candidate
    return None


def _is_valid_naics_code(code: str) -> bool:
    if code.isdigit() and 2 <= len(code) <= 6:
        return True
    parts = code.split("-")
    return (
        len(parts) == 2
        and all(part.isdigit() and len(part) == 2 for part in parts)
        and int(parts[0]) < int(parts[1])
    )


def _naics_level(code: str) -> int:
    if "-" in code:
        return 2
    return len(code)


def _sector_range_contains(range_code: str, sector_code: str) -> bool:
    if "-" not in range_code or not sector_code.isdigit():
        return False
    start, end = range_code.split("-", 1)
    return int(start) <= int(sector_code) <= int(end)


def _naics_notes(change_indicator: str | None, title_note: str | None) -> str | None:
    notes = []
    if change_indicator:
        notes.append(f"Change indicator: {change_indicator}.")
    if title_note:
        notes.append(title_note)
    return " ".join(notes) if notes else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    """CLI entry point for loading authoritative reference assets."""
    parser = argparse.ArgumentParser(
        description="Load authoritative geography and NAICS reference data."
    )
    parser.add_argument(
        "--database-path",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the SQLite database file.",
    )
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=DEFAULT_REFERENCE_DIR,
        help="Directory containing official reference assets.",
    )
    args = parser.parse_args()
    with connect_database(args.database_path) as connection:
        create_schema(connection)
        result = load_authoritative_reference_data(
            connection, reference_dir=args.reference_dir
        )
    print(
        "Loaded reference data: "
        f"ref_geography={result.ref_geography_count}, "
        "ref_geography_county_crosswalk="
        f"{result.ref_geography_county_crosswalk_count}, "
        f"ref_industry={result.ref_industry_count}, "
        f"manifests={len(result.manifest_ids)}"
    )


if __name__ == "__main__":
    main()
