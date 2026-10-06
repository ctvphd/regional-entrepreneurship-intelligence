# Assignment 7 Text Wireframes

These wireframes define information hierarchy, not UI code or final styling.

## 1. Executive Overview

```text
[Project title | purpose | research question | unit + period]
[AP 0.404] [Prevalence 0.233] [ROC-AUC 0.692] [Top-decile lift 1.99x]
[Development vs holdout fixed metrics       | Risk-decile / lift story]
[Top eligible risk pairs: MSA | sector | probability | horizon | coverage]
[What is an entrepreneurial gap? Numeric illustrative example]
[Explore regions] [Model diagnostics] [Data quality]
```

## 2. Regional & Industry Explorer

```text
[Search MSA] [Sector multiselect] [Year] [Risk category] [Observed gap]
[Selection coverage + eligibility note]
[Predicted t+3 risk and horizon] [Observed gap / alignment status]
[Observed vs expected startup activity: chart | numeric summary | explanation]
[Startup rate / employment growth / alignment history]
[Top N: 10 | 25 | 50] [Filtered table] [Download filtered CSV]
[Contextual data-quality and uncertainty note]
```

## 3. Model Performance

```text
[Fixed population view: development OOF / holdout, clearly labeled]
[Prevalence benchmark] [Logistic PRIMARY] [HGB SENSITIVITY]
[AP | ROC-AUC | Brier | recall | precision | F1]
[Precision-recall curve | ROC curve]
[Calibration curve / bins | lift and risk deciles]
[Year-by-year holdout | MSA-size holdout]
[Plain-language interpretation] [Technical methods expander]
```

## 4. Data Quality & Limitations

```text
[Coverage window + source availability]
[MSA coverage summary | sector coverage | eligible sample counts]
[Complete-case selection and exclusion differences]
[Missingness / suppression explanations]
[Sector and MSA-size performance caveats]
[Construct, calibration, temporal-generalization, non-causal warnings]
```

## 5. About / Methods / Sources

```text
[Project purpose | unit | years | research question]
[Sources and attribution table]
[Plain language: expected activity -> residual gap -> t+3 prediction]
[Model choice and holdout protocol]
[Technical details: formulas, features, cutoff, eligibility (expanders)]
[Data dictionary | version/model/data metadata | A6 commit]
[AI-use disclosure reference]
```
