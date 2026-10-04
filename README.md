# Regional Entrepreneurship Intelligence

## Project Overview

This research data project examines whether entrepreneurship keeps pace with regional industry growth. The Assignment 4 production database integrates federal business-demography, employment, regional-control, and business-pattern data into a documented metropolitan panel. It establishes a reproducible research dataset; it does not yet estimate alignment or make predictive claims.

**Unit of analysis:** MSA x industry x year. Each row represents one broad industry sector in one metropolitan statistical area for one calendar year.

**Study period:** 2010-2023.

## Data Sources

- **Business Dynamics Statistics (BDS), U.S. Census Bureau:** firm startups and business dynamics.
- **Quarterly Census of Employment and Wages (QCEW), U.S. Bureau of Labor Statistics:** employment, establishments, payroll, and industry growth.
- **American Community Survey (ACS), U.S. Census Bureau:** metropolitan population, income, education, labor-force participation, and unemployment controls.
- **County Business Patterns (CBP), U.S. Census Bureau:** supporting establishment, employment, and payroll measures aggregated from counties.

The current integrated production panel contains **63,577 rows, 381 MSAs, 19 broad sectors, and 14 years (2010-2023)**. It includes 5,887 MSA-sector panels: 2,830 are balanced over all 14 years and 3,057 are unbalanced. See [the analytical-panel documentation](docs/ANALYTICAL_PANEL.md) and [the merge audit](reports/assignment4_merge_audit.md) for coverage and missingness details.

## Architecture

The data flow is:

```text
reference -> raw -> staging -> intermediate -> analytics
```

Source-faithful raw values are retained. Staging records mapping, validity, and suppression information; intermediate tables apply source-specific geographic/industry rules and measures; the final panel uses an inner BDS-QCEW core with left-joined ACS and CBP support. The analytical key is `geography_id + industry_id + year`; display labels are available from `v_analytics_msa_industry_year`.

## Repository Structure

- `src/regional_entrepreneurship_intelligence/database/`: SQLite schema, reference loading, and run/quality metadata.
- `src/regional_entrepreneurship_intelligence/etl/`: source extract/load/transform runners and panel integration.
- `src/regional_entrepreneurship_intelligence/validation/`: reusable data checks.
- `tests/`: unit and integration-contract tests.
- `data/external/reference/`: small authoritative geography/industry workbooks and ACS concept registry.
- `data/raw/`: ignored source caches and production downloads.
- `data/processed/`: ignored generated analytical exports.
- `docs/`: architecture, source profiles, transformations, ERD, dictionary, and AI disclosure.
- `reports/`: committed QA documentation; generated details are normally ignored.
- `logs/`: ignored execution logs.

## Setup

Requirements: Python 3.10+, Git, and [UV](https://docs.astral.sh/uv/).

```powershell
git clone https://github.com/ctvphd/regional-entrepreneurship-intelligence.git
Set-Location regional-entrepreneurship-intelligence
uv sync
uv run python --version
```

## Production Pipeline

The documented end-to-end command is:

```powershell
uv run python -m regional_entrepreneurship_intelligence.etl.run_pipeline
```

By default this is cache-only and fails before changing the database if any required national production input is missing. Restore the ignored production files from the project’s approved storage first. To allow the existing source acquisition code to retrieve missing inputs, pass `--allow-downloads`; the Census API sources may require `CENSUS_API_KEY` in the environment. To select another SQLite file:

```powershell
uv run python -m regional_entrepreneurship_intelligence.etl.run_pipeline --database-path .\database\review.sqlite
```

The default SQLite database is `database/assignment4_production.sqlite`. The runner loads committed reference assets, executes BDS, QCEW, ACS, and CBP stages, integrates and validates the analytical panel, updates the merge audit/export, and writes a timestamped log under `logs/`. It prints a JSON run summary and exits nonzero on a failed stage.

## Tests

```powershell
uv run python -m unittest discover -s tests -v
```

## Data And Reproducibility Policy

Full national source files, the multi-gigabyte production database, generated exports, and run logs are Git-ignored. This keeps source data and local execution artifacts out of the repository; small official samples and reference assets remain available for review and tests. Source manifests record endpoints, vintages, checksums, filenames, and row counts. Pipeline runs, rejections, and quality metrics are stored in SQLite; generated logs record stage completion and failures. Transformations are designed for deterministic reruns, with production idempotency documented in the quality reports.

## Assignment Status

**Assignments 4 and 5 are complete.** Assignment 5 EDA uses the final 63,577-row analytical panel (381 MSAs, 19 sectors, 2010-2023). The synthesis is in [the final EDA report](reports/assignment5_final_eda_report.md), with [final review](reports/assignment5_final_review.md), [figure index](reports/assignment5_figure_index.md), [table index](reports/assignment5_table_index.md), and [requirements audit](reports/assignment5_final_rubric_audit.md).

Reproduce the complete EDA with:

```powershell
uv run --offline python -m regional_entrepreneurship_intelligence.analysis.run_eda
```

Assignment 6.1 design is complete, but model fitting has **not** begun. No expected-entrepreneurship estimates, alignment residuals, formal entrepreneurial-gap labels, future target columns, predictions, dashboards, or deployment artifacts have been created. See the [A6.1 design](docs/ASSIGNMENT6_DESIGN.md), [temporal folds](docs/ASSIGNMENT6_TEMPORAL_FOLDS.md), [leakage checklist](docs/ASSIGNMENT6_LEAKAGE_CHECKLIST.md), and [feature registry](docs/ASSIGNMENT6_FEATURE_REGISTRY.md). A6.2 remains unstarted.

## Documentation

- [Database architecture](docs/DATA_ARCHITECTURE.md)
- [Entity relationship diagram](docs/ERD.md)
- [Data dictionary](docs/data_dictionary.md)
- [Analytical panel](docs/ANALYTICAL_PANEL.md)
- [End-to-end pipeline guide](docs/PIPELINE.md)
- [Assignment 4 final rubric audit](reports/assignment4_final_rubric_audit.md)
- [Assignment 4 final quality report](reports/assignment4_final_quality_report.md)
- [Assignment 4 final review](reports/assignment4_final_review.md)
- Source profiles and transformations: [BDS](docs/BDS_SOURCE_PROFILE.md), [QCEW](docs/QCEW_SOURCE_PROFILE.md), [ACS](docs/ACS_SOURCE_PROFILE.md), [CBP](docs/CBP_SOURCE_PROFILE.md)
- [AI use disclosure](docs/AI_USE.md)

## AI Use

AI-assisted work and student-directed decisions are documented in [docs/AI_USE.md](docs/AI_USE.md).

## License

This project is licensed under the MIT License; see [LICENSE](LICENSE).
