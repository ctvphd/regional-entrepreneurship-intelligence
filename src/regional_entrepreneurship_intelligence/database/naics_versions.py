"""Auditable source-year NAICS vintages and conservative sector concordance."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from regional_entrepreneurship_intelligence.database.reference import (
    DEFAULT_REFERENCE_DIR,
    _xlsx_rows,
)


TARGET_VERSION = "2022"
COMBINED_SECTORS = {"31", "32", "33", "44", "45", "48", "49"}
PRIVATE_BROAD_SECTORS = (
    "11", "21", "22", "23", "31-33", "42", "44-45", "48-49", "51", "52",
    "53", "54", "55", "56", "61", "62", "71", "72", "81",
)


@dataclass(frozen=True)
class SourceYearNAICS:
    source: str
    year: int
    native_version: str
    target_version: str
    mapping_requirement: str
    notes: str


def source_year_naics(source: str, year: int) -> SourceYearNAICS:
    if not 2010 <= year <= 2023:
        raise ValueError(f"Year outside study window: {year}")
    if source == "BDS":
        native = "2017"
        notes = "2023 BDS release classifies the historical series using 2017 NAICS."
    elif source == "QCEW":
        native = "2007" if year == 2010 else "2012" if year <= 2016 else "2017" if year <= 2021 else "2022"
        notes = "BLS QCEW published classification for the source year."
    elif source == "CBP":
        native = "2007" if year <= 2011 else "2012" if year <= 2016 else "2017"
        notes = "Census CBP API NAICS field for the source year."
    else:
        raise ValueError(f"Unknown NAICS source: {source}")
    return SourceYearNAICS(
        source=source,
        year=year,
        native_version=native,
        target_version=TARGET_VERSION,
        mapping_requirement="none" if native == TARGET_VERSION else "official_concordance_audit",
        notes=notes,
    )


def sector_of(naics_code: str) -> str:
    prefix = str(naics_code)[:2]
    if prefix in {"31", "32", "33"}:
        return "31-33"
    if prefix in {"44", "45"}:
        return "44-45"
    if prefix in {"48", "49"}:
        return "48-49"
    return prefix


def _edges(path: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for row in _xlsx_rows(path)[3:]:
        if len(row) < 3:
            continue
        old, new = row[0].strip(), row[2].strip()
        if old.isdigit() and new.isdigit() and len(old) == len(new) == 6:
            result[old].add(new)
    return dict(result)


@lru_cache(maxsize=4)
def _sector_relations(version: str, reference_dir: str) -> dict[str, set[str]]:
    root = Path(reference_dir)
    steps = {
        "2007": ("2007_to_2012_naics.xls", "2012_to_2017_NAICS.xlsx", "2017_to_2022_NAICS.xlsx"),
        "2012": ("2012_to_2017_NAICS.xlsx", "2017_to_2022_NAICS.xlsx"),
        "2017": ("2017_to_2022_NAICS.xlsx",),
    }
    if version == TARGET_VERSION:
        return {}
    if version not in steps:
        raise ValueError(f"Unsupported NAICS vintage: {version}")
    maps = [_edges(root / name) for name in steps[version]]
    for prior, following in zip(maps, maps[1:]):
        missing = {code for destinations in prior.values() for code in destinations} - set(following)
        if missing:
            raise ValueError(f"Official NAICS chain has {len(missing)} unmapped handoff codes")
    relations: dict[str, set[str]] = defaultdict(set)
    for old in maps[0]:
        current = {old}
        for mapping in maps:
            current = {new for code in current for new in mapping.get(code, ())}
            if not current:
                raise ValueError(f"Official NAICS chain ended before 2022 for {old}")
        relations[sector_of(old)].update(sector_of(code) for code in current)
    return dict(relations)


@lru_cache(maxsize=4)
def _target_sectors(reference_dir: str) -> set[str]:
    return {sector_of(new) for destinations in _edges(
        Path(reference_dir) / "2017_to_2022_NAICS.xlsx"
    ).values() for new in destinations}


def classify_sector(
    native_version: str,
    source_sector: str,
    reference_dir: str | Path = DEFAULT_REFERENCE_DIR,
) -> tuple[str, str | None]:
    """Accept only reciprocal one-sector concordance relationships."""
    root = str(Path(reference_dir).resolve())
    if native_version == TARGET_VERSION:
        return (("directly_comparable", source_sector) if source_sector in _target_sectors(root)
                else ("unresolved", None))
    relations = _sector_relations(native_version, root)
    targets = relations.get(source_sector, set())
    if len(targets) != 1:
        return "unresolved", None
    target = next(iter(targets))
    source_sectors = {old for old, mapped in relations.items() if target in mapped}
    if source_sectors != {source_sector}:
        return "unresolved", None
    return (
        "directly_comparable" if source_sector == target else "official_mapping_required",
        target,
    )
