# Data Dictionary

This skeleton data dictionary is generated from the Assignment 4.2 SQLite schema. Raw source fields are provisional until live source ingestion verifies the exact source columns.

Assignment 4.3 adds deterministic seed helpers for the reference and metadata framework. `ref_year` is populated with exactly the 2010-2023 primary study window, and `ref_source` is populated with the four approved source systems.

Assignment 4.4 loads authoritative Census reference files. `ref_geography` uses the July 2023 CBSA delineation vintage, `ref_geography_county_crosswalk` preserves county-to-CBSA membership, and `ref_industry` uses the 2022 NAICS structure as the analytical reference version. Official 2012/2017/2022 NAICS concordance files are preserved for later source-specific mapping, but no speculative crosswalk mappings are applied in A4.4.

| Table | Field | Type | Key status | Nullable? | Source | Definition | Important business rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `analytics_msa_industry_year` | `geography_id` | INTEGER | PK, FK -> ref_geography.geography_id | No | integrated analytics | Surrogate key for standardized geography. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `industry_id` | INTEGER | PK, FK -> ref_industry.industry_id | No | integrated analytics | Surrogate key for standardized industry. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `year` | INTEGER | PK, FK -> ref_year.year | No | integrated analytics | Calendar year. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `startup_rate` | REAL |  | Yes | integrated analytics | Startup rate measure. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `lagged_startup_rate` | REAL |  | Yes | integrated analytics | Lagged startup rate for historical feature construction. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `employment` | REAL |  | Yes | integrated analytics | Employment level. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `establishments` | REAL |  | Yes | integrated analytics | Establishment count. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `payroll` | REAL |  | Yes | integrated analytics | Payroll or wage total. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `average_wage` | REAL |  | Yes | integrated analytics | Average wage or average pay measure. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `employment_growth` | REAL |  | Yes | integrated analytics | Employment growth measure. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `establishment_growth` | REAL |  | Yes | integrated analytics | Establishment growth measure. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `payroll_growth` | REAL |  | Yes | integrated analytics | Payroll growth measure. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `wage_growth` | REAL |  | Yes | integrated analytics | Wage or average-pay growth measure. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `population` | REAL |  | Yes | integrated analytics | Population estimate or measure. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `median_household_income` | REAL |  | Yes | integrated analytics | Median household income measure. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `educational_attainment_pct` | REAL |  | Yes | integrated analytics | Educational attainment percentage. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `labor_force_participation_pct` | REAL |  | Yes | integrated analytics | Labor-force participation percentage. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `unemployment_rate` | REAL |  | Yes | integrated analytics | Unemployment rate. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `business_structure_establishments` | REAL |  | Yes | integrated analytics | CBP-derived establishments measure carried into analytics. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `business_structure_employment` | REAL |  | Yes | integrated analytics | CBP-derived employment measure carried into analytics. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `has_suppression` | INTEGER |  | No | integrated analytics | Boolean-like indicator that one or more contributing values are suppressed. | Signals contribution from suppressed inputs. |
| `analytics_msa_industry_year` | `source_quality_notes` | TEXT |  | Yes | integrated analytics | Notes about source quality for the analytical row. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `analytics_msa_industry_year` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | integrated analytics | Identifier for a pipeline run or stage run. | Do not store global expected entrepreneurship, residual alignment, or final gap target. |
| `int_business_structure` | `geography_id` | INTEGER | PK, FK -> ref_geography.geography_id | No | CBP-derived intermediate | Surrogate key for standardized geography. |  |
| `int_business_structure` | `industry_id` | INTEGER | PK, FK -> ref_industry.industry_id | No | CBP-derived intermediate | Surrogate key for standardized industry. |  |
| `int_business_structure` | `year` | INTEGER | PK, FK -> ref_year.year | No | CBP-derived intermediate | Calendar year. |  |
| `int_business_structure` | `establishments` | REAL |  | Yes | CBP-derived intermediate | Establishment count. |  |
| `int_business_structure` | `employment` | REAL |  | Yes | CBP-derived intermediate | Employment level. |  |
| `int_business_structure` | `annual_payroll` | REAL |  | Yes | CBP-derived intermediate | Annual payroll measure from CBP. |  |
| `int_business_structure` | `first_quarter_payroll` | REAL |  | Yes | CBP-derived intermediate | First-quarter payroll measure from CBP. |  |
| `int_business_structure` | `has_suppression` | INTEGER |  | No | CBP-derived intermediate | Boolean-like indicator that one or more contributing values are suppressed. | Signals contribution from suppressed inputs. |
| `int_business_structure` | `source_manifest_id` | INTEGER | FK -> metadata_source_manifest.manifest_id | Yes | CBP-derived intermediate | Manifest identifier for the source artifact contributing to a derived row. |  |
| `int_business_structure` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | CBP-derived intermediate | Identifier for a pipeline run or stage run. |  |
| `int_business_structure` | `notes` | TEXT |  | Yes | CBP-derived intermediate | Free-text notes. |  |
| `int_entrepreneurship` | `geography_id` | INTEGER | PK, FK -> ref_geography.geography_id | No | BDS-derived intermediate | Surrogate key for standardized geography. |  |
| `int_entrepreneurship` | `industry_id` | INTEGER | PK, FK -> ref_industry.industry_id | No | BDS-derived intermediate | Surrogate key for standardized industry. |  |
| `int_entrepreneurship` | `year` | INTEGER | PK, FK -> ref_year.year | No | BDS-derived intermediate | Calendar year. |  |
| `int_entrepreneurship` | `firm_startups` | REAL |  | Yes | BDS-derived intermediate | Firm startup count or measure when available. |  |
| `int_entrepreneurship` | `startup_rate` | REAL |  | Yes | BDS-derived intermediate | Startup rate measure. |  |
| `int_entrepreneurship` | `establishment_entry` | REAL |  | Yes | BDS-derived intermediate | Establishment entry or births measure. |  |
| `int_entrepreneurship` | `startup_job_creation` | REAL |  | Yes | BDS-derived intermediate | Startup-related job creation measure. |  |
| `int_entrepreneurship` | `lagged_startup_rate` | REAL |  | Yes | BDS-derived intermediate | Lagged startup rate for historical feature construction. |  |
| `int_entrepreneurship` | `has_suppression` | INTEGER |  | No | BDS-derived intermediate | Boolean-like indicator that one or more contributing values are suppressed. | Signals contribution from suppressed inputs. |
| `int_entrepreneurship` | `source_manifest_id` | INTEGER | FK -> metadata_source_manifest.manifest_id | Yes | BDS-derived intermediate | Manifest identifier for the source artifact contributing to a derived row. |  |
| `int_entrepreneurship` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | BDS-derived intermediate | Identifier for a pipeline run or stage run. |  |
| `int_entrepreneurship` | `notes` | TEXT |  | Yes | BDS-derived intermediate | Free-text notes. |  |
| `int_industry_growth` | `geography_id` | INTEGER | PK, FK -> ref_geography.geography_id | No | QCEW-derived intermediate | Surrogate key for standardized geography. |  |
| `int_industry_growth` | `industry_id` | INTEGER | PK, FK -> ref_industry.industry_id | No | QCEW-derived intermediate | Surrogate key for standardized industry. |  |
| `int_industry_growth` | `year` | INTEGER | PK, FK -> ref_year.year | No | QCEW-derived intermediate | Calendar year. |  |
| `int_industry_growth` | `employment` | REAL |  | Yes | QCEW-derived intermediate | Employment level. |  |
| `int_industry_growth` | `establishments` | REAL |  | Yes | QCEW-derived intermediate | Establishment count. |  |
| `int_industry_growth` | `payroll` | REAL |  | Yes | QCEW-derived intermediate | Payroll or wage total. |  |
| `int_industry_growth` | `average_wage` | REAL |  | Yes | QCEW-derived intermediate | Average wage or average pay measure. |  |
| `int_industry_growth` | `employment_growth` | REAL |  | Yes | QCEW-derived intermediate | Employment growth measure. |  |
| `int_industry_growth` | `establishment_growth` | REAL |  | Yes | QCEW-derived intermediate | Establishment growth measure. |  |
| `int_industry_growth` | `payroll_growth` | REAL |  | Yes | QCEW-derived intermediate | Payroll growth measure. |  |
| `int_industry_growth` | `wage_growth` | REAL |  | Yes | QCEW-derived intermediate | Wage or average-pay growth measure. |  |
| `int_industry_growth` | `is_real_adjusted` | INTEGER |  | No | QCEW-derived intermediate | Boolean-like indicator that monetary values have been inflation adjusted. |  |
| `int_industry_growth` | `has_suppression` | INTEGER |  | No | QCEW-derived intermediate | Boolean-like indicator that one or more contributing values are suppressed. | Signals contribution from suppressed inputs. |
| `int_industry_growth` | `source_manifest_id` | INTEGER | FK -> metadata_source_manifest.manifest_id | Yes | QCEW-derived intermediate | Manifest identifier for the source artifact contributing to a derived row. |  |
| `int_industry_growth` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | QCEW-derived intermediate | Identifier for a pipeline run or stage run. |  |
| `int_industry_growth` | `notes` | TEXT |  | Yes | QCEW-derived intermediate | Free-text notes. |  |
| `int_regional_controls` | `geography_id` | INTEGER | PK, FK -> ref_geography.geography_id | No | ACS-derived intermediate | Surrogate key for standardized geography. |  |
| `int_regional_controls` | `year` | INTEGER | PK, FK -> ref_year.year | No | ACS-derived intermediate | Calendar year. |  |
| `int_regional_controls` | `population` | REAL |  | Yes | ACS-derived intermediate | Population estimate or measure. |  |
| `int_regional_controls` | `population_growth` | REAL |  | Yes | ACS-derived intermediate | Population growth measure. |  |
| `int_regional_controls` | `median_household_income` | REAL |  | Yes | ACS-derived intermediate | Median household income measure. |  |
| `int_regional_controls` | `educational_attainment_pct` | REAL |  | Yes | ACS-derived intermediate | Educational attainment percentage. |  |
| `int_regional_controls` | `labor_force_participation_pct` | REAL |  | Yes | ACS-derived intermediate | Labor-force participation percentage. |  |
| `int_regional_controls` | `unemployment_rate` | REAL |  | Yes | ACS-derived intermediate | Unemployment rate. |  |
| `int_regional_controls` | `has_suppression` | INTEGER |  | No | ACS-derived intermediate | Boolean-like indicator that one or more contributing values are suppressed. | Signals contribution from suppressed inputs. |
| `int_regional_controls` | `source_manifest_id` | INTEGER | FK -> metadata_source_manifest.manifest_id | Yes | ACS-derived intermediate | Manifest identifier for the source artifact contributing to a derived row. |  |
| `int_regional_controls` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | ACS-derived intermediate | Identifier for a pipeline run or stage run. |  |
| `int_regional_controls` | `notes` | TEXT |  | Yes | ACS-derived intermediate | Free-text notes. |  |
| `metadata_pipeline_run` | `pipeline_run_id` | TEXT | PK | No | pipeline metadata | Identifier for a pipeline run or stage run. |  |
| `metadata_pipeline_run` | `start_timestamp` | TEXT |  | No | pipeline metadata | Pipeline run start timestamp. |  |
| `metadata_pipeline_run` | `end_timestamp` | TEXT |  | Yes | pipeline metadata | Pipeline run end timestamp. |  |
| `metadata_pipeline_run` | `status` | TEXT |  | No | pipeline metadata | Pipeline run status. |  |
| `metadata_pipeline_run` | `stage` | TEXT |  | No | pipeline metadata | Pipeline stage name. |  |
| `metadata_pipeline_run` | `records_read` | INTEGER |  | Yes | pipeline metadata | Number of records read. |  |
| `metadata_pipeline_run` | `records_written` | INTEGER |  | Yes | pipeline metadata | Number of records written. |  |
| `metadata_pipeline_run` | `records_rejected` | INTEGER |  | Yes | pipeline metadata | Number of records rejected. |  |
| `metadata_pipeline_run` | `warnings` | TEXT |  | Yes | pipeline metadata | Warning messages from a run. |  |
| `metadata_pipeline_run` | `error_message` | TEXT |  | Yes | pipeline metadata | Error message when a run fails or partially fails. |  |
| `metadata_source_manifest` | `manifest_id` | INTEGER | PK | No | pipeline metadata | Surrogate key for source retrieval manifest. |  |
| `metadata_source_manifest` | `source_id` | INTEGER | FK -> ref_source.source_id | Yes | pipeline metadata | Surrogate key for a source registry entry. |  |
| `metadata_source_manifest` | `source_name` | TEXT |  | No | pipeline metadata | Name of source dataset or source system. |  |
| `metadata_source_manifest` | `source_agency` | TEXT |  | Yes | pipeline metadata | Agency responsible for the source. |  |
| `metadata_source_manifest` | `dataset_name` | TEXT |  | Yes | pipeline metadata | Dataset name within the source agency. |  |
| `metadata_source_manifest` | `access_method` | TEXT |  | Yes | pipeline metadata | Actual retrieval method for a source artifact. |  |
| `metadata_source_manifest` | `source_url_or_endpoint` | TEXT |  | Yes | pipeline metadata | URL or endpoint used for retrieval. |  |
| `metadata_source_manifest` | `retrieval_timestamp` | TEXT |  | Yes | pipeline metadata | Timestamp when the source artifact was retrieved. |  |
| `metadata_source_manifest` | `source_year` | INTEGER |  | Yes | pipeline metadata | Year represented by the source artifact or row. |  |
| `metadata_source_manifest` | `source_version` | TEXT |  | Yes | pipeline metadata | Source version or release label. |  |
| `metadata_source_manifest` | `raw_filename` | TEXT |  | Yes | pipeline metadata | Stored raw filename. |  |
| `metadata_source_manifest` | `file_checksum` | TEXT |  | Yes | pipeline metadata | Checksum for retrieved raw artifact. |  |
| `metadata_source_manifest` | `row_count` | INTEGER |  | Yes | pipeline metadata | Number of rows in the retrieved artifact. |  |
| `metadata_source_manifest` | `notes` | TEXT |  | Yes | pipeline metadata | Free-text notes. |  |
| `quality_rejected_record` | `rejection_id` | INTEGER | PK | No | quality metadata | Primary key for rejected-record tracking. |  |
| `quality_rejected_record` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | quality metadata | Identifier for a pipeline run or stage run. |  |
| `quality_rejected_record` | `source_id` | INTEGER | FK -> ref_source.source_id | Yes | quality metadata | Surrogate key for a source registry entry. |  |
| `quality_rejected_record` | `table_name` | TEXT |  | No | quality metadata | Table associated with a quality record or metric. |  |
| `quality_rejected_record` | `stage` | TEXT |  | No | quality metadata | Pipeline stage name. |  |
| `quality_rejected_record` | `source_row_identifier` | TEXT |  | Yes | quality metadata | Identifier for a row within a source artifact. |  |
| `quality_rejected_record` | `reason_code` | TEXT |  | No | quality metadata | Standardized reason code for rejected or reviewed record. |  |
| `quality_rejected_record` | `reason_detail` | TEXT |  | Yes | quality metadata | Detailed explanation for a rejected or reviewed record. |  |
| `quality_rejected_record` | `original_value` | TEXT |  | Yes | quality metadata | Original value associated with a rejected or reviewed record. |  |
| `quality_rejected_record` | `serialized_record` | TEXT |  | Yes | quality metadata | Serialized original record when appropriate and non-sensitive. | Avoid storing sensitive data unnecessarily. |
| `quality_rejected_record` | `created_timestamp` | TEXT |  | No | quality metadata | Timestamp when quality metadata was created. |  |
| `quality_table_metric` | `metric_id` | INTEGER | PK | No | quality metadata | Primary key for a quality metric. |  |
| `quality_table_metric` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | quality metadata | Identifier for a pipeline run or stage run. |  |
| `quality_table_metric` | `table_name` | TEXT |  | No | quality metadata | Table associated with a quality record or metric. |  |
| `quality_table_metric` | `metric_name` | TEXT |  | No | quality metadata | Name of quality metric. |  |
| `quality_table_metric` | `metric_value` | REAL |  | Yes | quality metadata | Numeric value for quality metric. |  |
| `quality_table_metric` | `year` | INTEGER |  | Yes | quality metadata | Calendar year. |  |
| `quality_table_metric` | `scope` | TEXT |  | Yes | quality metadata | Scope for quality metric. |  |
| `quality_table_metric` | `notes` | TEXT |  | Yes | quality metadata | Free-text notes. |  |
| `quality_table_metric` | `created_timestamp` | TEXT |  | No | quality metadata | Timestamp when quality metadata was created. |  |
| `raw_acs` | `raw_acs_id` | INTEGER | PK | No | ACS raw source - provisional, verify during source ingestion | Primary key for a raw ACS row. |  |
| `raw_acs` | `manifest_id` | INTEGER | FK -> metadata_source_manifest.manifest_id | Yes | ACS raw source - provisional, verify during source ingestion | Surrogate key for source retrieval manifest. |  |
| `raw_acs` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | ACS raw source - provisional, verify during source ingestion | Identifier for a pipeline run or stage run. |  |
| `raw_acs` | `source_year` | INTEGER |  | Yes | ACS raw source - provisional, verify during source ingestion | Year represented by the source artifact or row. |  |
| `raw_acs` | `source_geography_id` | TEXT |  | Yes | ACS raw source - provisional, verify during source ingestion | Source-native geography identifier; provisional - verify during source ingestion. |  |
| `raw_acs` | `source_industry_id` | TEXT |  | Yes | ACS raw source - provisional, verify during source ingestion | Source-native industry identifier; provisional - verify during source ingestion. |  |
| `raw_acs` | `source_naics_version` | TEXT |  | Yes | ACS raw source - provisional, verify during source ingestion | Source-native NAICS vintage/version; provisional - verify during source ingestion. |  |
| `raw_acs` | `source_row_identifier` | TEXT |  | Yes | ACS raw source - provisional, verify during source ingestion | Identifier for a row within a source artifact. |  |
| `raw_acs` | `raw_source_filename` | TEXT |  | Yes | ACS raw source - provisional, verify during source ingestion | Raw source filename associated with a row. |  |
| `raw_acs` | `is_suppressed` | INTEGER |  | Yes | ACS raw source - provisional, verify during source ingestion | Boolean-like indicator that a value or row is suppressed. | Suppression is not zero; preserve separately from missingness. |
| `raw_acs` | `raw_payload` | TEXT |  | Yes | ACS raw source - provisional, verify during source ingestion | Serialized source-native row payload; provisional - verify during source ingestion. | Preserve source fidelity; do not treat as final analytical field. |
| `raw_acs` | `notes` | TEXT |  | Yes | ACS raw source - provisional, verify during source ingestion | Free-text notes. |  |
| `raw_bds` | `raw_bds_id` | INTEGER | PK | No | BDS raw source - provisional, verify during source ingestion | Primary key for a raw BDS row. |  |
| `raw_bds` | `manifest_id` | INTEGER | FK -> metadata_source_manifest.manifest_id | Yes | BDS raw source - provisional, verify during source ingestion | Surrogate key for source retrieval manifest. |  |
| `raw_bds` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | BDS raw source - provisional, verify during source ingestion | Identifier for a pipeline run or stage run. |  |
| `raw_bds` | `source_year` | INTEGER |  | Yes | BDS raw source - provisional, verify during source ingestion | Year represented by the source artifact or row. |  |
| `raw_bds` | `source_geography_id` | TEXT |  | Yes | BDS raw source - provisional, verify during source ingestion | Source-native geography identifier; provisional - verify during source ingestion. |  |
| `raw_bds` | `source_industry_id` | TEXT |  | Yes | BDS raw source - provisional, verify during source ingestion | Source-native industry identifier; provisional - verify during source ingestion. |  |
| `raw_bds` | `source_naics_version` | TEXT |  | Yes | BDS raw source - provisional, verify during source ingestion | Source-native NAICS vintage/version; provisional - verify during source ingestion. |  |
| `raw_bds` | `source_row_identifier` | TEXT |  | Yes | BDS raw source - provisional, verify during source ingestion | Identifier for a row within a source artifact. |  |
| `raw_bds` | `raw_source_filename` | TEXT |  | Yes | BDS raw source - provisional, verify during source ingestion | Raw source filename associated with a row. |  |
| `raw_bds` | `is_suppressed` | INTEGER |  | Yes | BDS raw source - provisional, verify during source ingestion | Boolean-like indicator that a value or row is suppressed. | Suppression is not zero; preserve separately from missingness. |
| `raw_bds` | `raw_payload` | TEXT |  | Yes | BDS raw source - provisional, verify during source ingestion | Serialized source-native row payload; provisional - verify during source ingestion. | Preserve source fidelity; do not treat as final analytical field. |
| `raw_bds` | `notes` | TEXT |  | Yes | BDS raw source - provisional, verify during source ingestion | Free-text notes. |  |
| `raw_cbp` | `raw_cbp_id` | INTEGER | PK | No | CBP raw source - provisional, verify during source ingestion | Primary key for a raw CBP row. |  |
| `raw_cbp` | `manifest_id` | INTEGER | FK -> metadata_source_manifest.manifest_id | Yes | CBP raw source - provisional, verify during source ingestion | Surrogate key for source retrieval manifest. |  |
| `raw_cbp` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | CBP raw source - provisional, verify during source ingestion | Identifier for a pipeline run or stage run. |  |
| `raw_cbp` | `source_year` | INTEGER |  | Yes | CBP raw source - provisional, verify during source ingestion | Year represented by the source artifact or row. |  |
| `raw_cbp` | `source_geography_id` | TEXT |  | Yes | CBP raw source - provisional, verify during source ingestion | Source-native geography identifier; provisional - verify during source ingestion. |  |
| `raw_cbp` | `source_industry_id` | TEXT |  | Yes | CBP raw source - provisional, verify during source ingestion | Source-native industry identifier; provisional - verify during source ingestion. |  |
| `raw_cbp` | `source_naics_version` | TEXT |  | Yes | CBP raw source - provisional, verify during source ingestion | Source-native NAICS vintage/version; provisional - verify during source ingestion. |  |
| `raw_cbp` | `source_row_identifier` | TEXT |  | Yes | CBP raw source - provisional, verify during source ingestion | Identifier for a row within a source artifact. |  |
| `raw_cbp` | `raw_source_filename` | TEXT |  | Yes | CBP raw source - provisional, verify during source ingestion | Raw source filename associated with a row. |  |
| `raw_cbp` | `is_suppressed` | INTEGER |  | Yes | CBP raw source - provisional, verify during source ingestion | Boolean-like indicator that a value or row is suppressed. | Suppression is not zero; preserve separately from missingness. |
| `raw_cbp` | `raw_payload` | TEXT |  | Yes | CBP raw source - provisional, verify during source ingestion | Serialized source-native row payload; provisional - verify during source ingestion. | Preserve source fidelity; do not treat as final analytical field. |
| `raw_cbp` | `notes` | TEXT |  | Yes | CBP raw source - provisional, verify during source ingestion | Free-text notes. |  |
| `raw_qcew` | `raw_qcew_id` | INTEGER | PK | No | QCEW raw source - provisional, verify during source ingestion | Primary key for a raw QCEW row. |  |
| `raw_qcew` | `manifest_id` | INTEGER | FK -> metadata_source_manifest.manifest_id | Yes | QCEW raw source - provisional, verify during source ingestion | Surrogate key for source retrieval manifest. |  |
| `raw_qcew` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | QCEW raw source - provisional, verify during source ingestion | Identifier for a pipeline run or stage run. |  |
| `raw_qcew` | `source_year` | INTEGER |  | Yes | QCEW raw source - provisional, verify during source ingestion | Year represented by the source artifact or row. |  |
| `raw_qcew` | `source_geography_id` | TEXT |  | Yes | QCEW raw source - provisional, verify during source ingestion | Source-native geography identifier; provisional - verify during source ingestion. |  |
| `raw_qcew` | `source_industry_id` | TEXT |  | Yes | QCEW raw source - provisional, verify during source ingestion | Source-native industry identifier; provisional - verify during source ingestion. |  |
| `raw_qcew` | `source_naics_version` | TEXT |  | Yes | QCEW raw source - provisional, verify during source ingestion | Source-native NAICS vintage/version; provisional - verify during source ingestion. |  |
| `raw_qcew` | `source_row_identifier` | TEXT |  | Yes | QCEW raw source - provisional, verify during source ingestion | Identifier for a row within a source artifact. |  |
| `raw_qcew` | `raw_source_filename` | TEXT |  | Yes | QCEW raw source - provisional, verify during source ingestion | Raw source filename associated with a row. |  |
| `raw_qcew` | `is_suppressed` | INTEGER |  | Yes | QCEW raw source - provisional, verify during source ingestion | Boolean-like indicator that a value or row is suppressed. | Suppression is not zero; preserve separately from missingness. |
| `raw_qcew` | `raw_payload` | TEXT |  | Yes | QCEW raw source - provisional, verify during source ingestion | Serialized source-native row payload; provisional - verify during source ingestion. | Preserve source fidelity; do not treat as final analytical field. |
| `raw_qcew` | `notes` | TEXT |  | Yes | QCEW raw source - provisional, verify during source ingestion | Free-text notes. |  |
| `ref_geography` | `geography_id` | INTEGER | PK | No | reference | Surrogate key for standardized geography. |  |
| `ref_geography` | `cbsa_code` | TEXT |  | No | reference | Standardized CBSA code for MSA or micropolitan geography. |  |
| `ref_geography` | `cbsa_name` | TEXT |  | No | reference | Standardized CBSA or geography name. |  |
| `ref_geography` | `geography_type` | TEXT |  | No | reference | Type of geography represented by the row. |  |
| `ref_geography` | `state_codes` | TEXT |  | Yes | reference | State abbreviations associated with the geography. |  |
| `ref_geography` | `valid_from_year` | INTEGER |  | Yes | reference | First year for which the reference row applies. |  |
| `ref_geography` | `valid_to_year` | INTEGER |  | Yes | reference | Last year for which the reference row applies. |  |
| `ref_geography` | `source_vintage` | TEXT |  | No | reference | Vintage or source release used for the reference row. |  |
| `ref_geography` | `is_active` | INTEGER |  | No | reference | Boolean-like indicator for active reference values. |  |
| `ref_geography` | `notes` | TEXT |  | Yes | reference | Free-text notes. |  |
| `ref_industry` | `industry_id` | INTEGER | PK | No | reference | Surrogate key for standardized industry. |  |
| `ref_industry` | `naics_code` | TEXT |  | No | reference | NAICS code. |  |
| `ref_industry` | `naics_level` | INTEGER |  | No | reference | NAICS digit level. |  |
| `ref_industry` | `naics_title` | TEXT |  | No | reference | NAICS industry title. |  |
| `ref_industry` | `naics_version` | TEXT |  | No | reference | NAICS vintage/version. |  |
| `ref_industry` | `parent_naics_code` | TEXT |  | Yes | reference | Parent NAICS code where applicable. |  |
| `ref_industry` | `is_active` | INTEGER |  | No | reference | Boolean-like indicator for active reference values. |  |
| `ref_industry` | `notes` | TEXT |  | Yes | reference | Free-text notes. |  |
| `ref_source` | `source_id` | INTEGER | PK | No | source registry | Surrogate key for a source registry entry. |  |
| `ref_source` | `source_name` | TEXT |  | No | source registry | Name of source dataset or source system. |  |
| `ref_source` | `source_agency` | TEXT |  | Yes | source registry | Agency responsible for the source. |  |
| `ref_source` | `dataset_name` | TEXT |  | Yes | source registry | Dataset name within the source agency. |  |
| `ref_source` | `default_access_method` | TEXT |  | Yes | source registry | Default planned acquisition method. |  |
| `ref_source` | `homepage_url` | TEXT |  | Yes | source registry | Source homepage URL when documented. |  |
| `ref_source` | `notes` | TEXT |  | Yes | source registry | Free-text notes. |  |
| `ref_year` | `year` | INTEGER | PK | No | deterministic reference | Calendar year. |  |
| `ref_year` | `is_primary_study_year` | INTEGER |  | No | deterministic reference | Boolean-like marker for 2010-2023 primary study window. |  |
| `ref_year` | `notes` | TEXT |  | Yes | deterministic reference | Free-text notes. |  |
| `stg_acs` | `stg_acs_id` | INTEGER | PK | No | ACS staging | Primary key for a staged ACS row. |  |
| `stg_acs` | `raw_acs_id` | INTEGER | FK -> raw_acs.raw_acs_id | Yes | ACS staging | Primary key for a raw ACS row. |  |
| `stg_acs` | `manifest_id` | INTEGER | FK -> metadata_source_manifest.manifest_id | Yes | ACS staging | Surrogate key for source retrieval manifest. |  |
| `stg_acs` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | ACS staging | Identifier for a pipeline run or stage run. |  |
| `stg_acs` | `geography_id` | INTEGER | FK -> ref_geography.geography_id | Yes | ACS staging | Surrogate key for standardized geography. |  |
| `stg_acs` | `year` | INTEGER | FK -> ref_year.year | Yes | ACS staging | Calendar year. |  |
| `stg_acs` | `population` | REAL |  | Yes | ACS staging | Population estimate or measure. |  |
| `stg_acs` | `median_household_income` | REAL |  | Yes | ACS staging | Median household income measure. |  |
| `stg_acs` | `educational_attainment_pct` | REAL |  | Yes | ACS staging | Educational attainment percentage. |  |
| `stg_acs` | `labor_force_participation_pct` | REAL |  | Yes | ACS staging | Labor-force participation percentage. |  |
| `stg_acs` | `unemployment_rate` | REAL |  | Yes | ACS staging | Unemployment rate. |  |
| `stg_acs` | `is_missing` | INTEGER |  | Yes | ACS staging | Boolean-like indicator that a value is missing. | Missingness is not suppression and is not true zero. |
| `stg_acs` | `is_suppressed` | INTEGER |  | Yes | ACS staging | Boolean-like indicator that a value or row is suppressed. | Suppression is not zero; preserve separately from missingness. |
| `stg_acs` | `notes` | TEXT |  | Yes | ACS staging | Free-text notes. |  |
| `stg_bds` | `stg_bds_id` | INTEGER | PK | No | BDS staging | Primary key for a staged BDS row. |  |
| `stg_bds` | `raw_bds_id` | INTEGER | FK -> raw_bds.raw_bds_id | Yes | BDS staging | Primary key for a raw BDS row. |  |
| `stg_bds` | `manifest_id` | INTEGER | FK -> metadata_source_manifest.manifest_id | Yes | BDS staging | Surrogate key for source retrieval manifest. |  |
| `stg_bds` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | BDS staging | Identifier for a pipeline run or stage run. |  |
| `stg_bds` | `geography_id` | INTEGER | FK -> ref_geography.geography_id | Yes | BDS staging | Surrogate key for standardized geography. |  |
| `stg_bds` | `industry_id` | INTEGER | FK -> ref_industry.industry_id | Yes | BDS staging | Surrogate key for standardized industry. |  |
| `stg_bds` | `year` | INTEGER | FK -> ref_year.year | Yes | BDS staging | Calendar year. |  |
| `stg_bds` | `firm_startups` | REAL |  | Yes | BDS staging | Firm startup count or measure when available. |  |
| `stg_bds` | `startup_rate` | REAL |  | Yes | BDS staging | Startup rate measure. |  |
| `stg_bds` | `establishment_entry` | REAL |  | Yes | BDS staging | Establishment entry or births measure. |  |
| `stg_bds` | `startup_job_creation` | REAL |  | Yes | BDS staging | Startup-related job creation measure. |  |
| `stg_bds` | `is_missing` | INTEGER |  | Yes | BDS staging | Boolean-like indicator that a value is missing. | Missingness is not suppression and is not true zero. |
| `stg_bds` | `is_suppressed` | INTEGER |  | Yes | BDS staging | Boolean-like indicator that a value or row is suppressed. | Suppression is not zero; preserve separately from missingness. |
| `stg_bds` | `notes` | TEXT |  | Yes | BDS staging | Free-text notes. |  |
| `stg_cbp` | `stg_cbp_id` | INTEGER | PK | No | CBP staging | Primary key for a staged CBP row. |  |
| `stg_cbp` | `raw_cbp_id` | INTEGER | FK -> raw_cbp.raw_cbp_id | Yes | CBP staging | Primary key for a raw CBP row. |  |
| `stg_cbp` | `manifest_id` | INTEGER | FK -> metadata_source_manifest.manifest_id | Yes | CBP staging | Surrogate key for source retrieval manifest. |  |
| `stg_cbp` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | CBP staging | Identifier for a pipeline run or stage run. |  |
| `stg_cbp` | `geography_id` | INTEGER | FK -> ref_geography.geography_id | Yes | CBP staging | Surrogate key for standardized geography. |  |
| `stg_cbp` | `industry_id` | INTEGER | FK -> ref_industry.industry_id | Yes | CBP staging | Surrogate key for standardized industry. |  |
| `stg_cbp` | `year` | INTEGER | FK -> ref_year.year | Yes | CBP staging | Calendar year. |  |
| `stg_cbp` | `establishments` | REAL |  | Yes | CBP staging | Establishment count. |  |
| `stg_cbp` | `employment` | REAL |  | Yes | CBP staging | Employment level. |  |
| `stg_cbp` | `annual_payroll` | REAL |  | Yes | CBP staging | Annual payroll measure from CBP. |  |
| `stg_cbp` | `first_quarter_payroll` | REAL |  | Yes | CBP staging | First-quarter payroll measure from CBP. |  |
| `stg_cbp` | `is_missing` | INTEGER |  | Yes | CBP staging | Boolean-like indicator that a value is missing. | Missingness is not suppression and is not true zero. |
| `stg_cbp` | `is_suppressed` | INTEGER |  | Yes | CBP staging | Boolean-like indicator that a value or row is suppressed. | Suppression is not zero; preserve separately from missingness. |
| `stg_cbp` | `notes` | TEXT |  | Yes | CBP staging | Free-text notes. |  |
| `stg_qcew` | `stg_qcew_id` | INTEGER | PK | No | QCEW staging | Primary key for a staged QCEW row. |  |
| `stg_qcew` | `raw_qcew_id` | INTEGER | FK -> raw_qcew.raw_qcew_id | Yes | QCEW staging | Primary key for a raw QCEW row. |  |
| `stg_qcew` | `manifest_id` | INTEGER | FK -> metadata_source_manifest.manifest_id | Yes | QCEW staging | Surrogate key for source retrieval manifest. |  |
| `stg_qcew` | `pipeline_run_id` | TEXT | FK -> metadata_pipeline_run.pipeline_run_id | Yes | QCEW staging | Identifier for a pipeline run or stage run. |  |
| `stg_qcew` | `geography_id` | INTEGER | FK -> ref_geography.geography_id | Yes | QCEW staging | Surrogate key for standardized geography. |  |
| `stg_qcew` | `industry_id` | INTEGER | FK -> ref_industry.industry_id | Yes | QCEW staging | Surrogate key for standardized industry. |  |
| `stg_qcew` | `year` | INTEGER | FK -> ref_year.year | Yes | QCEW staging | Calendar year. |  |
| `stg_qcew` | `employment` | REAL |  | Yes | QCEW staging | Employment level. |  |
| `stg_qcew` | `establishments` | REAL |  | Yes | QCEW staging | Establishment count. |  |
| `stg_qcew` | `payroll` | REAL |  | Yes | QCEW staging | Payroll or wage total. |  |
| `stg_qcew` | `average_pay` | REAL |  | Yes | QCEW staging | Average annual pay from QCEW staging. |  |
| `stg_qcew` | `is_missing` | INTEGER |  | Yes | QCEW staging | Boolean-like indicator that a value is missing. | Missingness is not suppression and is not true zero. |
| `stg_qcew` | `is_suppressed` | INTEGER |  | Yes | QCEW staging | Boolean-like indicator that a value or row is suppressed. | Suppression is not zero; preserve separately from missingness. |
| `stg_qcew` | `notes` | TEXT |  | Yes | QCEW staging | Free-text notes. |  |

## A4.4 Maintained Addendum

The generated A4.2 dictionary is supplemented by the A4.4 county crosswalk and reference-loading decisions below.

| Table | Field | Type | Key status | Nullable? | Source | Definition | Important business rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ref_geography_county_crosswalk` | `county_crosswalk_id` | INTEGER | PK | No | Census CBSA List 1 | Primary key for a county membership row. | One row per CBSA x county x source vintage. |
| `ref_geography_county_crosswalk` | `geography_id` | INTEGER | FK -> ref_geography.geography_id | No | Census CBSA List 1 | Surrogate key for the parent CBSA record. | Must match the same source vintage represented by the parent CBSA. |
| `ref_geography_county_crosswalk` | `cbsa_code` | TEXT | Unique key component | No | Census CBSA List 1 | Five-digit CBSA code. | Used with `county_geoid` and `source_vintage` to prevent duplicate memberships. |
| `ref_geography_county_crosswalk` | `county_name` | TEXT |  | No | Census CBSA List 1 | County or county-equivalent name. | Preserve official file spelling. |
| `ref_geography_county_crosswalk` | `state_name` | TEXT |  | No | Census CBSA List 1 | State or territory name. | Preserve official file spelling. |
| `ref_geography_county_crosswalk` | `state_fips` | TEXT |  | No | Census CBSA List 1 | Two-digit state FIPS code. | Store as text to preserve leading zeroes. |
| `ref_geography_county_crosswalk` | `county_fips` | TEXT |  | No | Census CBSA List 1 | Three-digit county FIPS code. | Store as text to preserve leading zeroes. |
| `ref_geography_county_crosswalk` | `county_geoid` | TEXT | Unique key component | No | Census CBSA List 1 | Five-digit state-plus-county GEOID. | Derived directly from state and county FIPS values in the official file. |
| `ref_geography_county_crosswalk` | `central_outlying` | TEXT |  | Yes | Census CBSA List 1 | Central or outlying county classification. | Values constrained to `Central` or `Outlying` when present. |
| `ref_geography_county_crosswalk` | `source_vintage` | TEXT | Unique key component | No | Census CBSA List 1 | Reference vintage label. | A4.4 uses `July 2023 CBSA delineation`. |
| `ref_geography_county_crosswalk` | `notes` | TEXT |  | Yes | Project metadata | Free-text provenance notes. | Does not replace manifest-level source metadata. |
| `raw_bds` | `source_year` | INTEGER |  | Yes | BDS bulk CSV `year` | BDS source-native year. | A4.5 sample is restricted to 2010-2023; no lag construction is performed. |
| `raw_bds` | `source_geography_id` | TEXT |  | Yes | BDS bulk CSV `msa` | BDS source-native MSA code. | Do not assume direct compatibility with July 2023 CBSA until A4.6 mapping review. |
| `raw_bds` | `source_industry_id` | TEXT |  | Yes | BDS bulk CSV `sector` | BDS source-native sector code, including combined sectors where present. | Do not assume direct compatibility with 2022 NAICS until A4.6 mapping review. |
| `raw_bds` | `source_naics_version` | TEXT |  | Yes | Project metadata | Text note identifying that the raw value is BDS source-native sector coding. | This is not a standardized NAICS version assignment. |
| `raw_bds` | `source_row_identifier` | TEXT |  | Yes | Project loader | Deterministic source-native row identifier built from BDS file, year, MSA, and sector. | Used by the loader to avoid duplicate raw sample rows on rerun. |
| `raw_bds` | `is_suppressed` | INTEGER |  | Yes | BDS source values | Boolean-like indicator set when source row contains `D` or `S` values. | `D`, `N`, `S`, and `X` values remain preserved in `raw_payload`; numeric values are not coerced to zero. |
| `raw_bds` | `raw_payload` | TEXT |  | Yes | BDS bulk CSV row | JSON serialization of the complete source-native BDS row. | Raw layer preserves source fidelity and does not derive startup rates. |

## A4.6 Maintained Addendum

A4.6 adds BDS firm-age raw ingestion, mapping-status fields, startup construction, and lag fields.

| Table | Field | Type | Key status | Nullable? | Source | Definition | Important business rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `raw_bds_firm_age` | `raw_bds_firm_age_id` | INTEGER | PK | No | BDS firm-age sample | Primary key for a source-native BDS firm-age row. | Preserves the MSA-sector-firm-age grain. |
| `raw_bds_firm_age` | `source_fagecoarse` | TEXT |  | Yes | BDS `fagecoarse` | Source-native firm-age-coarse category. | Age-0 startup category is `a) 0`; do not infer other categories. |
| `raw_bds_firm_age` | `source_naics_version` | TEXT |  | Yes | Project metadata | Notes that BDS sector coding is treated as 2017 NAICS. | Does not convert to 2022 NAICS. |
| `raw_bds_firm_age` | `raw_payload` | TEXT |  | Yes | BDS firm-age CSV row | JSON serialization of the complete source-native row. | `D`, `N`, `S`, and `X` values remain source-faithful. |
| `stg_bds` | `source_geography_id` | TEXT |  | Yes | BDS `msa` | Source-native BDS MSA code. | Mapping audit classifies but does not manually fix codes. |
| `stg_bds` | `source_industry_id` | TEXT |  | Yes | BDS `sector` | Source-native BDS sector code. | Combined sectors are preserved. |
| `stg_bds` | `source_fagecoarse` | TEXT |  | Yes | BDS `fagecoarse` | Source-native firm-age category used for startup construction. | A4.6 uses age-0 rows only. |
| `stg_bds` | `geography_mapping_status` | TEXT |  | Yes | Mapping audit | Direct-match/crosswalk-required/unresolved geography status. | Unresolved rows are retained in staging and excluded from intermediate construction. |
| `stg_bds` | `industry_mapping_status` | TEXT |  | Yes | Mapping audit | Directly-comparable/official-mapping-required/unresolved industry status. | Blanket 2017-to-2022 conversion is not performed. |
| `stg_bds` | `startup_rate` | REAL |  | Yes | Derived from BDS age-0 and backbone rows | Age-0 firms divided by all firms in the same MSA-sector-year, multiplied by 100. | Null when numerator or denominator is suppressed, unavailable, nonnumeric, or zero. |
| `stg_bds` | `establishment_entry_rate` | REAL |  | Yes | BDS MSA-sector backbone | Supporting establishment entry rate. | Robustness/supporting measure, not the primary startup definition. |
| `int_entrepreneurship` | `startup_rate_lag1` | REAL |  | Yes | Derived after standardization | Prior calendar-year startup rate within geography-industry panel. | Null if year `t - 1` is missing or suppressed. |
| `int_entrepreneurship` | `startup_rate_lag2` | REAL |  | Yes | Derived after standardization | Two-year lagged startup rate within geography-industry panel. | Null if year `t - 2` is missing or suppressed. |
| `int_entrepreneurship` | `startup_rate_lag3` | REAL |  | Yes | Derived after standardization | Three-year lagged startup rate within geography-industry panel. | Null if year `t - 3` is missing or suppressed. |

## A4.7 Maintained Addendum

A4.7 verifies QCEW annual CSV source fields and expands `raw_qcew` from provisional identifiers to source-faithful annual area fields. No `stg_qcew`, `int_industry_growth`, growth-rate, or lag construction is performed in A4.7.

| Table | Field | Type | Key status | Nullable? | Source | Definition | Important business rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `raw_qcew` | `source_geography_id` | TEXT |  | Yes | QCEW `area_fips` | Source-native QCEW area code. | Preserve as text. A4.8 should aggregate county rows to July 2023 CBSA through `ref_geography_county_crosswalk` before analysis. |
| `raw_qcew` | `source_industry_id` | TEXT |  | Yes | QCEW `industry_code` | Source-native QCEW industry code. | Preserve native QCEW coding; do not assume direct 2022 NAICS comparability until mapping review. |
| `raw_qcew` | `source_naics_version` | TEXT |  | Yes | Project metadata | Source-vintage note for QCEW industry coding. | A4.7 stores `QCEW source-native NAICS-based industry_code`; source-to-2022 classification is deferred. |
| `raw_qcew` | `source_ownership_code` | TEXT |  | Yes | QCEW `own_code` | Source-native ownership category. | Recommended A4.8 analytical scope is private sector, `own_code = 5`; do not combine totals with ownership-specific rows. |
| `raw_qcew` | `source_size_code` | TEXT |  | Yes | QCEW `size_code` | Source-native QCEW establishment-size category. | Included in the raw grain and source row identifier. |
| `raw_qcew` | `disclosure_code` | TEXT |  | Yes | QCEW `disclosure_code` | Source disclosure/status code. | Nonblank disclosure/status values set `is_suppressed = 1`; preserve original values in `raw_payload`. |
| `raw_qcew` | `annual_avg_estabs` | TEXT |  | Yes | QCEW annual CSV | Annual average establishment count as published. | Raw layer keeps source text; numeric casting belongs in staging. |
| `raw_qcew` | `annual_avg_emplvl` | TEXT |  | Yes | QCEW annual CSV | Annual average employment level as published. | Raw layer keeps source text; numeric casting belongs in staging. |
| `raw_qcew` | `total_annual_wages` | TEXT |  | Yes | QCEW annual CSV | Total annual wages as published. | Raw layer keeps source text; monetary adjustment is deferred. |
| `raw_qcew` | `avg_annual_pay` | TEXT |  | Yes | QCEW annual CSV | Average annual pay as published. | Raw layer keeps source text; growth and inflation adjustment are deferred. |
| `raw_qcew` | `source_row_identifier` | TEXT |  | Yes | Project loader | Deterministic identifier built from year, `area_fips`, `own_code`, `industry_code`, `size_code`, and `qtr`. | Used to make raw sample ingestion idempotent. |

## A4.8 Maintained Addendum

A4.8 expands QCEW staging and intermediate documentation for county-to-CBSA aggregation, nominal measures, growth, and lags.

| Table | Field | Type | Key status | Nullable? | Source | Definition | Important business rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `stg_qcew` | `source_geography_id` | TEXT |  | Yes | QCEW `area_fips` | Comma-separated county GEOIDs contributing to the aggregated CBSA-sector-year row. | Preserve lineage for county aggregation. |
| `stg_qcew` | `source_ownership_code` | TEXT |  | Yes | QCEW `own_code` | Ownership code selected for staging. | A4.8 uses private ownership only, `5`. |
| `stg_qcew` | `ownership_scope` | TEXT |  | Yes | Project rule | Human-readable ownership scope. | Do not mix total ownership with ownership-specific rows. |
| `stg_qcew` | `geography_mapping_status` | TEXT |  | Yes | Mapping audit | QCEW geography mapping status. | County rows mapped through July 2023 crosswalk use `crosswalk_required`. |
| `stg_qcew` | `industry_mapping_status` | TEXT |  | Yes | Mapping audit | QCEW industry mapping status. | Exact 2022 sector matches are `directly_comparable`; unresolved source codes are retained in quality metadata. |
| `stg_qcew` | `total_annual_wages_nominal` | REAL |  | Yes | Aggregated QCEW | Sum of county total annual wages. | Nominal dollars; no deflator applied in A4.8. |
| `stg_qcew` | `average_annual_pay_nominal` | REAL |  | Yes | Derived after aggregation | Recalculated average annual pay. | `round(total_annual_wages_nominal / employment)` when denominator is valid. |
| `stg_qcew` | `counties_expected` | INTEGER |  | Yes | July 2023 county crosswalk | Number of counties expected for the CBSA. | Used to flag partial coverage. |
| `stg_qcew` | `counties_observed` | INTEGER |  | Yes | QCEW raw rows | Number of contributing source counties observed. | Must equal expected counties for complete aggregation. |
| `stg_qcew` | `counties_suppressed` | INTEGER |  | Yes | QCEW disclosure flags | Number of contributing counties with suppression/status flags. | Suppressed counties are not treated as zero. |
| `int_industry_growth` | `total_annual_wages_nominal` | REAL |  | Yes | `stg_qcew` | Nominal annual wages at CBSA-sector-year grain. | Not real-adjusted. |
| `int_industry_growth` | `average_annual_pay_nominal` | REAL |  | Yes | `stg_qcew` | Nominal average annual pay at CBSA-sector-year grain. | Recalculated after county aggregation. |
| `int_industry_growth` | `employment_growth` | REAL |  | Yes | Derived | Annual employment growth. | Null when prior calendar year or valid denominator is unavailable. |
| `int_industry_growth` | `establishment_growth` | REAL |  | Yes | Derived | Annual establishment growth. | Null when prior calendar year or valid denominator is unavailable. |
| `int_industry_growth` | `payroll_growth` | REAL |  | Yes | Derived | Annual nominal payroll growth. | Do not label as real growth. |
| `int_industry_growth` | `wage_growth` | REAL |  | Yes | Derived | Annual nominal average-pay growth. | Do not label as real growth. |
| `int_industry_growth` | `employment_growth_lag1` | REAL |  | Yes | Derived | One-year lag of employment growth. | Requires actual `t - 1` year in same geography-industry panel. |
| `int_industry_growth` | `employment_growth_lag2` | REAL |  | Yes | Derived | Two-year lag of employment growth. | Requires actual `t - 2` year in same geography-industry panel. |
| `int_industry_growth` | `employment_growth_lag3` | REAL |  | Yes | Derived | Three-year lag of employment growth. | Requires actual `t - 3` year in same geography-industry panel. |
| `int_industry_growth` | `establishment_growth_lag1` | REAL |  | Yes | Derived | One-year lag of establishment growth. | Requires actual `t - 1` year in same geography-industry panel. |
| `int_industry_growth` | `establishment_growth_lag2` | REAL |  | Yes | Derived | Two-year lag of establishment growth. | Requires actual `t - 2` year in same geography-industry panel. |
| `int_industry_growth` | `establishment_growth_lag3` | REAL |  | Yes | Derived | Three-year lag of establishment growth. | Requires actual `t - 3` year in same geography-industry panel. |

## A4.9 Maintained Addendum

A4.9 expands ACS raw, staging, and intermediate documentation for source variables, MOEs, MSA-year regional controls, population growth, and one-year lags.

| Table | Field | Type | Key status | Nullable? | Source | Definition | Important business rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `raw_acs` | `source_geography_name` | TEXT |  | Yes | ACS `NAME` | Source geography label. | Preserve source label; do not map by name alone. |
| `raw_acs` | `source_variable_id` | TEXT |  | Yes | ACS API | Estimate variable ID. | Required for source lineage. |
| `raw_acs` | `source_moe_variable_id` | TEXT |  | Yes | ACS API | Margin-of-error variable ID. | Preserve ACS uncertainty metadata. |
| `raw_acs` | `source_product` | TEXT |  | Yes | ACS API | ACS product name. | A4.9 uses ACS 5-year Data Profile. |
| `raw_acs` | `control_name` | TEXT |  | Yes | Project mapping | Canonical regional-control name. | Used to pivot raw variables to staging. |
| `raw_acs` | `estimate_value` | TEXT |  | Yes | ACS API | Source estimate as text. | Raw layer keeps source values. |
| `raw_acs` | `margin_of_error` | TEXT |  | Yes | ACS API | Source MOE as text. | Special negative Census codes are preserved in raw. |
| `stg_acs` | `source_geography_id` | TEXT |  | Yes | ACS geography code | Source-native MSA/CBSA code. | Audited against July 2023 CBSA reference. |
| `stg_acs` | `geography_mapping_status` | TEXT |  | Yes | Mapping audit | Direct/crosswalk/unresolved status. | Unresolved rows are retained in staging and excluded from intermediate controls. |
| `stg_acs` | `population_moe` | REAL |  | Yes | ACS MOE variable | MOE for population where available. | Census special negative MOE codes become null in staging. |
| `stg_acs` | `median_household_income_moe` | REAL |  | Yes | ACS MOE variable | MOE for median household income. | Preserved for transparency; intermediate uses point estimates. |
| `stg_acs` | `educational_attainment_pct_moe` | REAL |  | Yes | ACS MOE variable | MOE for bachelor-degree-or-higher percentage. | Percent estimates must remain within 0-100. |
| `stg_acs` | `labor_force_participation_pct_moe` | REAL |  | Yes | ACS MOE variable | MOE for labor-force participation percentage. | Percent estimates must remain within 0-100. |
| `stg_acs` | `unemployment_rate_moe` | REAL |  | Yes | ACS MOE variable | MOE for unemployment rate. | Percent estimates must remain within 0-100. |
| `int_regional_controls` | `population_growth` | REAL |  | Yes | Derived | Annual population growth. | Null when prior calendar year or valid denominator is unavailable. |
| `int_regional_controls` | `population_growth_lag1` | REAL |  | Yes | Derived | One-year lag of population growth. | Requires actual `t - 1` year within same MSA. |
| `int_regional_controls` | `median_household_income_lag1` | REAL |  | Yes | Derived | One-year lag of median household income. | Source-reported ACS dollars; not harmonized real dollars. |
| `int_regional_controls` | `educational_attainment_pct_lag1` | REAL |  | Yes | Derived | One-year lag of bachelor-degree-or-higher percentage. | No forward fill across missing years. |
| `int_regional_controls` | `labor_force_participation_pct_lag1` | REAL |  | Yes | Derived | One-year lag of labor-force participation percentage. | No cross-MSA leakage. |
| `int_regional_controls` | `unemployment_rate_lag1` | REAL |  | Yes | Derived | One-year lag of unemployment rate. | No cross-MSA leakage. |

## A4.10 Maintained Addendum

A4.10 verifies CBP API source fields and expands CBP raw, staging, and intermediate documentation for county identifiers, source flags, 2017 NAICS source coding, 2022 sector comparability, and complete county-coverage aggregation.

| Table | Field | Type | Key status | Nullable? | Source | Definition | Important business rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `raw_cbp` | `source_state_fips` | TEXT |  | Yes | CBP `state` | Two-digit source state FIPS code. | Preserve leading zeroes as text. |
| `raw_cbp` | `source_county_fips` | TEXT |  | Yes | CBP `county` | Three-digit source county FIPS code. | Preserve leading zeroes as text. |
| `raw_cbp` | `source_county_geoid` | TEXT |  | Yes | Derived from CBP `state` and `county` | Five-digit county GEOID. | Used for July 2023 CBSA county-crosswalk lookup. |
| `raw_cbp` | `source_industry_id` | TEXT |  | Yes | CBP `NAICS2017` | Source-native industry code. | A4.10 treats CBP source sectors as 2017 NAICS. |
| `raw_cbp` | `source_industry_label` | TEXT |  | Yes | CBP `NAICS2017_LABEL` | Source industry label. | Preserve Census label for audit. |
| `raw_cbp` | `source_naics_version` | TEXT |  | Yes | Project metadata | Source NAICS version note. | A4.10 stores `2017`; it does not relabel as 2022. |
| `raw_cbp` | `legal_form_code` | TEXT |  | Yes | CBP `LFO` | Legal-form code. | Sample uses `001` total legal forms. |
| `raw_cbp` | `employment_size_code` | TEXT |  | Yes | CBP `EMPSZES` | Employment-size code. | Sample uses `001` all sizes. |
| `raw_cbp` | `establishments` | TEXT |  | Yes | CBP `ESTAB` | Number of establishments as source text. | Numeric casting belongs in staging. |
| `raw_cbp` | `employment` | TEXT |  | Yes | CBP `EMP` | Employment as source text. | Numeric casting belongs in staging. |
| `raw_cbp` | `annual_payroll` | TEXT |  | Yes | CBP `PAYANN` | Annual payroll as source text. | Units are thousands of dollars. |
| `raw_cbp` | `first_quarter_payroll` | TEXT |  | Yes | CBP `PAYQTR1` | First-quarter payroll as source text. | Units are thousands of dollars. |
| `raw_cbp` | `establishments_flag` | TEXT |  | Yes | CBP `ESTAB_F` | Establishment source flag. | Nonblank flags set `is_suppressed = 1`. |
| `raw_cbp` | `employment_flag` | TEXT |  | Yes | CBP `EMP_F` | Employment source flag. | Flagged values are not treated as zero. |
| `raw_cbp` | `annual_payroll_flag` | TEXT |  | Yes | CBP `PAYANN_F` | Annual-payroll source flag. | Flagged values are retained in raw. |
| `raw_cbp` | `first_quarter_payroll_flag` | TEXT |  | Yes | CBP `PAYQTR1_F` | First-quarter-payroll source flag. | Flagged values are retained in raw. |
| `stg_cbp` | `source_county_geoid` | TEXT |  | Yes | `raw_cbp` | Source county GEOID retained in staging. | Staging remains county-level. |
| `stg_cbp` | `source_industry_id` | TEXT |  | Yes | `raw_cbp` | Source NAICS2017 industry code. | Do not overwrite with analytical sector code. |
| `stg_cbp` | `geography_mapping_status` | TEXT |  | Yes | Mapping audit | CBP county mapping status. | County rows mapped through July 2023 crosswalk use `crosswalk_required`. |
| `stg_cbp` | `industry_mapping_status` | TEXT |  | Yes | Mapping audit | CBP industry mapping status. | Exact 2022 sector matches are `directly_comparable`; source `00` is unresolved. |
| `stg_cbp` | `noise_or_suppression_flags` | TEXT |  | Yes | CBP flag fields | Serialized nonblank source flags. | Flagged rows do not advance to the intermediate layer. |
| `int_business_structure` | `standardized_cbsa_code` | TEXT |  | Yes | July 2023 CBSA reference | Analytical CBSA code. | Derived through county-to-CBSA crosswalk. |
| `int_business_structure` | `standardized_sector_code` | TEXT |  | Yes | 2022 NAICS reference | Analytical sector code. | Only directly comparable sectors enter A4.10 intermediate. |
| `int_business_structure` | `counties_expected` | INTEGER |  | Yes | July 2023 county crosswalk | Expected county count for the CBSA. | Used to enforce complete coverage. |
| `int_business_structure` | `counties_observed` | INTEGER |  | Yes | `stg_cbp` | Number of contributing counties observed. | Must equal expected counties for intermediate inclusion. |
| `int_business_structure` | `counties_suppressed` | INTEGER |  | Yes | `stg_cbp` flags | Number of contributing flagged counties. | Must be zero for intermediate inclusion. |
| `int_business_structure` | `is_complete_county_coverage` | INTEGER |  | Yes | Derived | Complete-coverage indicator. | A4.10 intermediate rows require value `1`. |
| `int_business_structure` | `geography_mapping_status` | TEXT |  | Yes | Mapping audit | Geography mapping status inherited from staging. | A4.10 intermediate rows use `crosswalk_required`. |
| `int_business_structure` | `industry_mapping_status` | TEXT |  | Yes | Mapping audit | Industry mapping status inherited from staging. | A4.10 intermediate rows use `directly_comparable`. |
