# Regional Entrepreneurship Intelligence

## Project Overview

This research project examines whether metropolitan industry opportunity predicts later startup activity below a model-based expectation. It integrates federal business-demography, employment, regional-control, and business-pattern data; evaluates a leakage-aware three-year-ahead prediction design; and communicates the historical results through a five-route dashboard. Claims are predictive/associational, not causal or live forecasts.

**Unit of analysis:** July 2023 CBSA/MSA x 2-digit 2022 NAICS industry x year.

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

## Repository Map

- `src/regional_entrepreneurship_intelligence/database/`: SQLite schema, reference loading, and run/quality metadata.
- `src/regional_entrepreneurship_intelligence/etl/`: source extract/load/transform runners and panel integration.
- `src/regional_entrepreneurship_intelligence/validation/`: reusable data checks.
- `src/regional_entrepreneurship_intelligence/dashboard/`: Streamlit routes, validated data loader, and dashboard health checks.
- `tests/`: unit, transformation, reproducibility, dashboard, and integration-contract tests.
- `tests/fixtures/reviewer_sources/`: seven fictional, source-shaped inputs for the clean-review fixture.
- `data/dashboard/`: frozen production dashboard artifacts (local/ignored).
- `data/review/`: generated synthetic review database and descriptive dashboard artifact (local/ignored).
- `database/`: production and local SQLite databases (ignored).
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

Production reproduction requires all **58 authorized local source-cache files**. The preflight is embedded at the start of the runner; it reports the exact missing paths and fails before database/log changes if any are absent. A safe read-only inventory command is:

```powershell
uv run python -c "from regional_entrepreneurship_intelligence.etl.run_pipeline import required_production_inputs; p=required_production_inputs(); n=sum(x.is_file() for x in p); print(f'Required: {len(p)}; present: {n}; missing: {len(p)-n}')"
```

The documented end-to-end command is:

```powershell
uv run python -m regional_entrepreneurship_intelligence.etl.run_pipeline
```

By default this is cache-only and fails before changing the database if any required national production input is missing. Restore the ignored production files from the project’s approved storage first. To allow the existing source acquisition code to retrieve missing inputs, pass `--allow-downloads`; the Census API sources may require `CENSUS_API_KEY` in the environment. To select another SQLite file:

```powershell
uv run python -m regional_entrepreneurship_intelligence.etl.run_pipeline --database-path .\database\review.sqlite
```

The default SQLite database is `database/assignment4_production.sqlite`. The runner loads committed reference assets, executes BDS, QCEW, ACS, and CBP stages, integrates and validates the analytical panel, updates the merge audit/export, and writes a timestamped log under `logs/`. Expected outputs are the production SQLite database, `data/processed/analytics_msa_industry_year.csv.gz`, `reports/assignment4_merge_audit.md`, and a run log. It prints a JSON run summary and exits nonzero on a failed stage. Do not run this command merely to verify the course submission; the production panel and frozen model outputs have already been evaluated.

## Tests

```powershell
uv run python -m unittest discover -s tests -v
```

## Reviewer Quickstart

```powershell
uv sync
uv run python -m regional_entrepreneurship_intelligence.review.build_reviewer_fixture
uv run --offline python -m unittest discover -s tests -v
```

This validates the end-to-end transformation and dashboard-integration path using fictional data. It does not reproduce the production empirical estimates. Restricted Windows sandboxes may need a writable `TEMP`/`TMP` directory; see [reviewer reproducibility](docs/REVIEWER_REPRODUCIBILITY.md) for current verification status. See also [fixture notes](tests/fixtures/reviewer_sources/README.md).

| Capability | Clean clone | Production cache required |
| --- | ---: | ---: |
| Unit tests | Yes | No |
| Synthetic end-to-end ETL | Yes | No |
| Review SQLite database | Yes | No |
| Dashboard descriptive-panel loader integration | Yes | No |
| Production 63,577-row panel | No | Yes |
| Final predictive metrics | No | Yes |
| Production dashboard artifacts | No | Yes |

## Data And Reproducibility Policy

Full national source files, the multi-gigabyte production database, generated exports, and run logs are Git-ignored. This keeps source data and local execution artifacts out of the repository; small official samples and reference assets remain available for review and tests. Source manifests record endpoints, vintages, checksums, filenames, and row counts. Pipeline runs, rejections, and quality metrics are stored in SQLite; generated logs record stage completion and failures. Transformations are designed for deterministic reruns, with production idempotency documented in the quality reports.

## Assignment Status

**Assignments 4-6 and A7.1-A7.8D are implemented; A7.10 closeout is partial.** The final temporal evaluation is documented in [the Assignment 6 report](reports/assignment6_final_analytics_engine.md), and the authoritative design/metrics are in [Final Research Design](docs/FINAL_RESEARCH_DESIGN.md). The current sandbox could not complete the full suite or browser route smoke QA; see [A7.10 integration report](reports/assignment7_final_integration.md). Production results require the authorized local source cache. See [reviewer reproducibility](docs/REVIEWER_REPRODUCIBILITY.md) and [professor feedback response](docs/PROFESSOR_FEEDBACK_RESPONSE.md).

Reproduce the complete EDA with:

```powershell
uv run --offline python -m regional_entrepreneurship_intelligence.analysis.run_eda
```

Assignment 7.9 is deferred optional portfolio work. A7.10 is **partial pending full-suite and browser-route verification**. No map, deployment, or containerization work was started.

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
- [Final research design and canonical metrics](docs/FINAL_RESEARCH_DESIGN.md)
- [Assignment 3-7 alignment](docs/PROJECT_ALIGNMENT_A3_A7.md)
- [Final limitations and strengths](docs/FINAL_LIMITATIONS_AND_STRENGTHS.md)
- [Final project summary](reports/final_project_summary.md)
- [A7.10 integration report](reports/assignment7_final_integration.md)
- [Final presentation outline](docs/FINAL_PRESENTATION_OUTLINE.md)

## AI Use

AI-assisted work and student-directed decisions are documented in [docs/AI_USE.md](docs/AI_USE.md).

## License

This project is licensed under the MIT License; see [LICENSE](LICENSE).
