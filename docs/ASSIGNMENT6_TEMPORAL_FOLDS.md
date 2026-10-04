# Assignment 6.1 Temporal Fold Specification

Primary validation uses expanding windows over exact same-MSA/same-sector t→t+3 calendar pairs. Counts below are observed key-contiguous panel pairs before complete-case feature filtering; no labels or future value columns are created by this specification.

| Split | Training predictor years | Training target years | Training outcome cutoff | Validation predictor years | Validation target years | Validation pairs | Training pairs | First-stage fit years | Final holdout |
|---|---|---|---:|---|---|---:|---:|---|---|
| Fold 1 | 2010-2013 | 2013-2016 | 2016 | 2014 | 2017 | 4,000 | 15,845 | 2010-2016 | no |
| Fold 2 | 2010-2014 | 2013-2017 | 2017 | 2015 | 2018 | 3,997 | 19,845 | 2010-2017 | no |
| Fold 3 | 2010-2015 | 2013-2018 | 2018 | 2016-2017 | 2019-2020 | 7,988 | 23,842 | 2010-2018 | no |
| Final holdout | 2010-2017 | 2013-2020 | 2020 | 2018-2020 | 2021-2023 | 12,091 | 31,830 | 2010-2020 | yes |

For each development fold, training labels end strictly before the first validation target year. Training expands with each fold. The final holdout is a single contiguous predictor block; no final holdout outcome may influence training, first-stage fitting, preprocessing, threshold selection, feature selection, or model choice.

The fold-local expected-entrepreneurship benchmark is trained only through the training-outcome cutoff. It is applied to target-year rows only to construct the residual outcome; target-year benchmark inputs are not predictive features at t. Each gap cutoff is learned from training residuals only and applied unchanged to validation/holdout residuals.

The latest targetable predictor year is `max(2010-2023) - 3 = 2020`. Actual pair counts by predictor year: 2010 3,959; 2011 3,986; 2012 3,945; 2013 3,955; 2014 4,000; 2015 3,997; 2016 4,011; 2017 3,977; 2018 4,001; 2019 4,070; 2020 4,020. Across all targetable years there are 43,921 key-contiguous pairs.

These boundaries are a proposed frozen design, not model performance results. A6.2 may report a genuine feasibility blocker, but may not change the locked three-year horizon or use ordinary random splitting as primary validation.
