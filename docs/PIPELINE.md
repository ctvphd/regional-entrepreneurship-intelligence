# Assignment 4 Pipeline

## End-To-End Command

From the repository root:

```powershell
uv run python -m regional_entrepreneurship_intelligence.etl.run_pipeline
```

The command is cache-only by default. It checks the production cache before opening the database and identifies missing files rather than substituting samples. To permit existing source runners to acquire missing files, opt in with `--allow-downloads`. `CENSUS_API_KEY` may be needed for Census API acquisition. `--database-path PATH` selects a different SQLite database.

## Stages

1. Create/update the schema and load committed July 2023 CBSA and 2022 NAICS references.
2. Run the production BDS, QCEW, ACS, and CBP acquisition/raw-load/standardization/intermediate stages using their existing modules.
3. Build `analytics_msa_industry_year`, its deterministic compressed export, and the merge audit.
4. Validate the analytical primary key, 2010-2023 year range, MSA-only scope, and absence of downstream leakage fields.
5. Save overall counts and rejected-record reason counts in the JSON console summary and log execution events to an ignored timestamped file under `logs/`.

Source-specific behavior is documented in `BDS_TRANSFORMATION.md`, `QCEW_TRANSFORMATION.md`, `ACS_TRANSFORMATION.md`, and `CBP_TRANSFORMATION.md`. A source-stage exception is surfaced with its stage in the log and fails the command. Inputs are never silently replaced with samples.

## Outputs

- SQLite tables and metadata: `database/assignment4_production.sqlite` by default (ignored).
- Compressed panel export: `data/processed/analytics_msa_industry_year.csv.gz` (ignored).
- Merge report: `reports/assignment4_merge_audit.md`.
- Execution log: `logs/assignment4_pipeline_<UTC timestamp>_<run id>.log` (ignored).

Manifests preserve source URLs, vintages, filenames, checksums, and row counts. Source-run metadata and panel quality metrics are stored in SQLite. Runners are rerunnable; complete end-to-end reruns are verified and summarized in `reports/assignment4_final_review.md`.
