# Assignment 7 Component Inventory

| Component | Overview | Explorer | Performance | Data Quality | About / Methods | Reuse notes |
| --- | --- | --- | --- | --- | --- | --- |
| Page title/short description | Yes | Yes | Yes | Yes | Yes | Shared page-header pattern. |
| KPI/metric strip | Holdout summary | Selected-row summary | Fixed metrics | Coverage totals | Study metadata | Include population/time role. |
| Searchable MSA selector | Link to Explorer | Primary filter | No | Optional drill-in | No | Explorer scope; preserve code/name. |
| Sector multiselect | Link to Explorer | Primary filter | No | Optional drill-in | No | Explorer scope. |
| Year selector | Context year | Primary filter | Fixed dev/holdout | Coverage period | Study period | Never conflate predictor and target. |
| Risk/gap filters | Top-risk universe note | Primary filters | No | No | No | Only eligible records with explicit role. |
| Plotly chart | Comparison/lift | Observed vs expected/trends | PR, ROC, calibration, lift | Coverage/selection | Optional methods diagram | Shared title/subtitle/takeaway/text-summary frame. |
| Data table | Top-risk preview | Filtered rows/Top N | Metric/subgroup | Coverage/selection | Sources/data dictionary | Show units, missingness, denominator, time role. |
| Explanatory callout | Gap explainer | Alignment/status | Metric interpretation | Limitations | Methods summary | Plain language first. |
| Warning/uncertainty note | Complete-case/holdout | Row-level coverage | Generalization/calibration | Persistent limitations | Scope caveat | Context-specific text using common pattern. |
| Expander | Optional methods | Metric definitions | Technical definitions | Audit details | Full methods/source notes | Keep technical detail secondary. |
| CSV download | No | Filtered CSV only | No | No | No | Exactly matches visible eligible filters. |
| Version/provenance block | Compact model/data | Score lineage | A6 artifact version | Source coverage | Full metadata | No local absolute paths. |
| Future map placeholder | None | Optional disabled note | None | None | Future-map spec link | No functional map in A7.1/A7. |

## Shared Reusable Patterns

- Year-role badge (`predictor year`, `target year`, `descriptive year`).
- Coverage indicator with explanatory text/count/rule, not color alone.
- Metric label/value/definition and fixed artifact provenance.
- Chart title/subtitle/takeaway plus accessible text summary.
- Concise caveat callout and expandable technical detail.
- Consistent percentage formatter and risk vocabulary.
