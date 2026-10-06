# Assignment 7.7 Data Quality, Coverage & Limitations

## Scope

Implemented only the Data Quality & Limitations page. It uses the validated A7.2 coverage, sector, MSA-size, and source artifacts, plus finalized A6 complete-case and geographic-generalization reporting tables. It does not read SQLite/raw inputs, change data/model outputs, or implement maps, A7.8, or About/Methods finalization.

## Page Content

- Coverage cards distinguish all 381 covered metropolitan areas, A5 comparison-eligible coverage, thin coverage, and MSAs with A6 OOF rows. The complete MSA table preserves all A7.2 coverage fields and supports sorting, search, and download.
- A sector support chart and table display final-holdout sample counts, positive outcomes, prevalence, the finalized sufficiency flag, and the source AP/ROC-AUC values. Suppressed metrics remain null.
- The complete-case section displays the frozen A6 validation fold inclusion counts and sample-selection audit. It highlights observed selection differences without calling the complete cases representative.
- Generalization includes fixed final-holdout MSA-size subgroup metrics and the pooled unseen-MSA development result from `a6_geographic_generalization.csv`, with split boundaries stated.
- Null/suppression semantics, the model-relative startup-gap construct, source catalog, lineage, reproducibility, and responsible-use limits are made explicit.

## Verification

Focused quality tests validate frozen audit contracts, expected coverage/sector rows, and Streamlit route rendering. Full `unittest` discovery passes 175 tests. Dashboard health passes; `uv lock --check` passes; the live `/quality` browser route renders with expected coverage cards, charts, tables, frozen audit summaries, and sources. Existing Overview/Performance metric reconciliation tests pass as part of the full suite. `pytest` itself is unavailable in the offline environment, so the complete suite was run through Python's unittest discovery.
