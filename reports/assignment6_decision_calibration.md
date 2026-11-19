# Assignment 6.8D: Decision Calibration and Business Rule

## Decision Context

A regional economic-development office cannot investigate every MSA-industry-year cell. The frozen Logistic score is used only to prioritize cases for deeper human review. It does not declare a market deficient, allocate funding, or recommend an intervention by itself.

## Selection Rules Evaluated

Top-fraction rules sort the frozen Logistic probabilities from highest to lowest and select the exact ceiling-sized workload. Probability ties at the boundary are resolved deterministically by MSA, sector, predictor year, and target year. This preserves an operationally exact case count and makes boundary handling reproducible.

| Rule | Flagged | True gaps | False positives | Precision | Recall | F1 | Lift | FP per TP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Top 5% | 516 | 274 | 242 | 53.1% | 11.4% | 0.188 | 2.28x | 0.88 |
| Top 10% | 1,031 | 476 | 555 | 46.2% | 19.9% | 0.278 | 1.99x | 1.17 |
| Top 15% | 1,546 | 648 | 898 | 41.9% | 27.0% | 0.329 | 1.80x | 1.39 |
| Top 20% | 2,061 | 838 | 1,223 | 40.7% | 35.0% | 0.376 | 1.75x | 1.46 |
| Top 25% | 2,576 | 993 | 1,583 | 38.5% | 41.4% | 0.399 | 1.66x | 1.59 |
| Top 30% | 3,092 | 1,151 | 1,941 | 37.2% | 48.0% | 0.419 | 1.60x | 1.69 |
| Development-prevalence threshold | 5,173 | 1,696 | 3,477 | 32.8% | 70.8% | 0.448 | 1.41x | 2.05 |

## Precision-Recall Tradeoff

The top 5% has the highest yield (53.1%) but captures only 11.4% of realized gaps. Expanding through 30% steadily increases captured gaps to 48.0%, while precision falls to 37.2%. Each capacity point exchanges workload and yield for broader early-warning coverage; none is universally optimal without an office-specific staffing constraint.

## False-Positive Burden

At the recommended top-10% rule, 555 of 1,031 reviewed cases (53.8%) are not realized gaps, or 1.17 non-gap cases per realized gap. The primary burden falls on analysts, regional economic-development staff, partner institutions, and local business-support organizations through follow-up research and opportunity cost. Communities may also bear outreach burden. These cases are screening costs, not necessarily useless reviews.

## False-Negative Cost

The top-10% queue leaves 1,920 realized gaps outside the selected group (80.1% of all gaps). A missed case may delay investigation of an emerging entrepreneurial shortfall, but this analysis does not establish that an intervention would have prevented or corrected it.

## Development-Prevalence Threshold

The committed threshold is 0.188347999. It flags 5,173 cases, including 1,696 realized gaps and 3,477 false positives. Precision is 32.8%, recall 70.8%, and lift 1.41x. The professor's approximate 5,173-case workload is confirmed. This rule captures many more gaps but asks staff to review half the holdout and produces 2.05 non-gap cases per realized gap.

## Sector and MSA-Size Concentration

The global top decile contains 13 sectors. The largest shares are 48-49 (19.2%), 71 (18.4%), 72 (13.7%), 61 (11.3%), 21 (9.5%). Mining is overrepresented (9.5% of flags versus 1.3% of rows), while Agriculture contributes 1.8% of flags. The queue is therefore concentrated, but not dominated only by the two highest-prevalence sectors.

- small: 394 flags (38.2% of flags versus 27.0% of holdout rows), 50.0% precision.
- middle: 361 flags (35.0% of flags versus 34.5% of holdout rows), 46.5% precision.
- large: 276 flags (26.8% of flags versus 38.5% of holdout rows), 40.2% precision.

Flags span 249 of 365 MSAs; the 10 MSAs with the largest flagged counts account for 11.1% of the queue. Concentration is diagnostic and is not itself evidence of unfairness or error.

## Recommended Operating Rule

Use the top 10% of frozen Logistic scores as the primary priority-review queue: 1,031 cases, 476 realized gaps, 555 false positives, 46.2% precision, 19.9% recall, 1.99x lift, and 1.17 false positives per true positive. This is preferred to top 5% because it captures substantially more gaps, and to broader rules because it retains nearly double-baseline yield at a clear, capacity-based workload.

If capacity permits, the next 10% can form a secondary monitoring queue rather than an automatic action tier. That incremental block contains 1,030 cases and 362 realized gaps (35.1% yield), adding 15.1% of all realized gaps. This sensitivity does not change the primary global ranking.

## Practical Interpretation

For every 100 top-decile cases reviewed, approximately 46 would be realized gaps and 54 would not. The queue captures about 19.9% of all realized gaps.

## Presentation-Ready Sentence

“If an economic-development office reviewed only the 10% of MSA-industry cases ranked highest risk, approximately 46% would be realized gaps, capturing 20% of all gaps at 1.99 times the overall prevalence.”

## Limitations

The operating rule is an ex post description of one three-year holdout, not a prospective impact evaluation. Precision may shift with future prevalence or data coverage. MSA-sector-year cells are not people, and complete-case coverage is weaker for some smaller metros. No monetary costs, intervention effects, causal claims, or probability recalibration are estimated. Human review should incorporate current local evidence before any action.
